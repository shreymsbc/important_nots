"""
Incremental ingestion pipeline for react_toolkit_knowledge.

Detects three change types automatically by comparing filesystem state
with what is stored in Qdrant (keyed on file_path + file_id):

  ADD    — file exists on disk but has no chunks in Qdrant yet
  UPDATE — file exists on disk but its content hash differs from the stored one
           → old chunks are deleted first, new chunks are embedded and upserted
  DELETE — file no longer exists on disk but chunks are still in Qdrant
           → all chunks for that file are removed

Run:
    python db/ingest.py             # full sync (add / update / delete)
    python db/ingest.py --dry-run   # print planned changes without executing
"""
import argparse
import hashlib
import logging
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from db.chunker import Chunk, chunk_markdown_file, chunk_react_file
from db.embedder import EmbeddingService
from db.schema import COLLECTION_NAME, ChunkMetadata, get_vector_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
CODES_DIR = ROOT_DIR / "codes"
MARKDOWN_DIR = ROOT_DIR / "markdown_files"
BATCH_SIZE = 64
QDRANT_URL = "http://localhost:6333"

_CODE_EXTENSIONS = ("*.jsx", "*.tsx", "*.js", "*.ts")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _file_id(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _get_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".tsx", ".ts"}:
        return "typescript"
    if ext in {".jsx", ".js"}:
        return "javascript"
    return "markdown"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT_DIR)).replace("\\", "/")


# ── Filesystem scanning ───────────────────────────────────────────────────────

@dataclass
class FileRecord:
    """Represents one source file found on disk."""
    path: Path
    rel_path: str
    fid: str
    source: str   # "codes" | "markdown_files"
    content: str


def _scan_filesystem() -> Dict[str, FileRecord]:
    """Return {rel_path: FileRecord} for every tracked file on disk."""
    records: Dict[str, FileRecord] = {}

    code_files = sorted(
        {fp for ext in _CODE_EXTENSIONS for fp in CODES_DIR.glob(ext)}
    )
    for path in code_files:
        content = path.read_text(encoding="utf-8")
        rp = _rel(path)
        records[rp] = FileRecord(path=path, rel_path=rp,
                                  fid=_file_id(content), source="codes",
                                  content=content)

    for path in sorted(MARKDOWN_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        rp = _rel(path)
        records[rp] = FileRecord(path=path, rel_path=rp,
                                  fid=_file_id(content), source="markdown_files",
                                  content=content)

    return records


# ── Qdrant state ──────────────────────────────────────────────────────────────

def _get_stored_files(client: QdrantClient) -> Dict[str, str]:
    """
    Scroll all points and return {rel_path: file_id} for every file that has
    at least one chunk stored in the collection.
    """
    stored: Dict[str, str] = {}
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=None,
            with_payload=["file_path", "file_id"],
            limit=256,
            offset=offset,
        )
        for r in records:
            pl = r.payload or {}
            fp = pl.get("file_path")
            fid = pl.get("file_id")
            if fp and fid and fp not in stored:
                stored[fp] = fid
        if offset is None:
            break
    return stored


def _delete_file_chunks(client: QdrantClient, fid: str, dry_run: bool = False) -> int:
    """Delete every point whose file_id matches *fid*.  Returns count deleted."""
    # First count how many points will be removed
    count_result = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(must=[FieldCondition(key="file_id", match=MatchValue(value=fid))]),
        exact=True,
    )
    n = count_result.count
    if dry_run or n == 0:
        return n
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="file_id", match=MatchValue(value=fid))]
        ),
    )
    return n


# ── Chunking + upserting ──────────────────────────────────────────────────────

def _build_chunks_for_file(rec: FileRecord) -> List[Tuple[Chunk, ChunkMetadata]]:
    """Chunk one file and build its ChunkMetadata objects."""
    try:
        if rec.source == "codes":
            chunks = chunk_react_file(str(rec.path))
        else:
            chunks = chunk_markdown_file(str(rec.path))
    except Exception as exc:
        logger.error("Failed to chunk %s: %s", rec.path.name, exc)
        return []

    total = len(chunks)
    results: List[Tuple[Chunk, ChunkMetadata]] = []
    for chunk in chunks:
        if rec.source == "codes":
            meta = ChunkMetadata(
                file_name=rec.path.name,
                file_path=rec.rel_path,
                file_id=rec.fid,
                file_type="code",
                language=_get_language(rec.path),
                component_name=chunk.component_name,
                chunk_id=chunk.chunk_id,
                chunk_type=chunk.chunk_type,
                chunk_index=chunk.chunk_index,
                total_chunks=total,
                source="codes",
                props=chunk.props,
                imports=chunk.imports,
                exports=chunk.exports,
            )
        else:
            meta = ChunkMetadata(
                file_name=rec.path.name,
                file_path=rec.rel_path,
                file_id=rec.fid,
                file_type="markdown",
                language="markdown",
                component_name=chunk.component_name,
                chunk_id=chunk.chunk_id,
                chunk_type=chunk.chunk_type,
                chunk_index=chunk.chunk_index,
                total_chunks=total,
                source="markdown_files",
            )
        results.append((chunk, meta))
    return results


def _upsert_chunks(
    client: QdrantClient,
    embedder: EmbeddingService,
    pairs: List[Tuple[Chunk, ChunkMetadata]],
    dry_run: bool = False,
) -> int:
    """Embed and upsert *pairs* in batches. Returns number of points upserted."""
    if not pairs or dry_run:
        return len(pairs)
    total_upserted = 0
    for batch_start in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[batch_start : batch_start + BATCH_SIZE]
        texts = [c.text for c, _ in batch]
        vectors = embedder.embed_texts(texts, task="search_document")
        points: List[PointStruct] = []
        for (chunk, meta), vector in zip(batch, vectors):
            payload = meta.to_dict()
            payload["text"] = chunk.text
            payload["text_hash"] = _text_hash(chunk.text)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        total_upserted += len(points)
    return total_upserted


# ── Collection setup ──────────────────────────────────────────────────────────

def _ensure_collection(client: QdrantClient) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        logger.info("Creating collection '%s'", COLLECTION_NAME)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=get_vector_config(),
        )
    else:
        logger.info("Collection '%s' already exists.", COLLECTION_NAME)


# ── Public sync entry-point ───────────────────────────────────────────────────

def sync(dry_run: bool = False) -> None:
    """
    Incremental sync: compare filesystem against Qdrant and
    apply ADD / UPDATE / DELETE changes automatically.

    Args:
        dry_run: When True, log what *would* happen but make no changes.
    """
    client = QdrantClient(url=QDRANT_URL)
    _ensure_collection(client)

    logger.info("Scanning filesystem...")
    fs_files: Dict[str, FileRecord] = _scan_filesystem()
    logger.info("Files on disk: %d", len(fs_files))

    logger.info("Reading Qdrant state...")
    stored_files: Dict[str, str] = _get_stored_files(client)
    logger.info("Files in Qdrant: %d", len(stored_files))

    # ── Classify every file ──────────────────────────────────────────────────
    to_add: List[FileRecord] = []
    to_update: List[FileRecord] = []
    to_delete: List[Tuple[str, str]] = []   # (rel_path, file_id)

    for rel_path, rec in fs_files.items():
        if rel_path not in stored_files:
            to_add.append(rec)
        elif stored_files[rel_path] != rec.fid:
            to_update.append(rec)
        # else: unchanged — skip

    for rel_path, fid in stored_files.items():
        if rel_path not in fs_files:
            to_delete.append((rel_path, fid))

    logger.info(
        "Plan — ADD: %d  UPDATE: %d  DELETE: %d  UNCHANGED: %d",
        len(to_add), len(to_update), len(to_delete),
        len(fs_files) - len(to_add) - len(to_update),
    )
    if dry_run:
        logger.info("[DRY-RUN] No changes will be written.")
        for r in to_add:
            logger.info("  [ADD]    %s", r.rel_path)
        for r in to_update:
            logger.info("  [UPDATE] %s", r.rel_path)
        for rp, _ in to_delete:
            logger.info("  [DELETE] %s", rp)
        return

    # ── Execute deletes (for UPDATE, delete old chunks first) ────────────────
    files_to_delete_chunks = list(to_delete)
    for rec in to_update:
        old_fid = stored_files[rec.rel_path]
        files_to_delete_chunks.append((rec.rel_path, old_fid))

    for rel_path, fid in files_to_delete_chunks:
        n = _delete_file_chunks(client, fid)
        logger.info("Deleted %d old chunks for: %s", n, rel_path)

    # ── Collect all new chunks to embed ──────────────────────────────────────
    all_new_pairs: List[Tuple[Chunk, ChunkMetadata]] = []
    for rec in to_add + to_update:
        logger.info("Chunking: %s", rec.rel_path)
        all_new_pairs.extend(_build_chunks_for_file(rec))

    if not all_new_pairs:
        logger.info("No new chunks to embed. Sync complete.")
        return

    logger.info("Embedding and upserting %d chunks...", len(all_new_pairs))
    embedder = EmbeddingService()
    n = _upsert_chunks(client, embedder, all_new_pairs)
    logger.info("Upserted %d points. Sync complete.", n)


# Keep `ingest` as an alias so existing integrations don't break
def ingest() -> None:
    sync(dry_run=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync codes/ and markdown_files/ into Qdrant."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing anything to Qdrant.",
    )
    args = parser.parse_args()
    sync(dry_run=args.dry_run)
