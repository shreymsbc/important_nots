import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from db.embedder import EmbeddingService
from db.schema import COLLECTION_NAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

QDRANT_URL = "http://localhost:6333"
TOP_K = 5

_ALLOWED_FILTER_FIELDS = {"file_type", "component_name", "source", "chunk_type", "language"}


def _build_filter(filter_dict: Optional[Dict[str, Any]]) -> Optional[Filter]:
    """Convert a plain dict into a Qdrant Filter with must-conditions."""
    if not filter_dict:
        return None
    conditions = []
    for field, value in filter_dict.items():
        if field not in _ALLOWED_FILTER_FIELDS:
            logger.warning("Ignoring unknown filter field: %s", field)
            continue
        conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
    return Filter(must=conditions) if conditions else None


def search(
    query: str,
    filter: Optional[Dict[str, Any]] = None,
    top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
    """
    Embed *query* and perform a cosine similarity search in Qdrant.

    Returns a flat list of hits, each with:
      - score:    cosine similarity
      - text:     the chunk text
      - metadata: all stored payload fields (file_id, chunk_index, props, …)

    Allowed filter keys: file_type, component_name, source, chunk_type, language.
    """
    embedder = EmbeddingService()
    logger.info("Embedding query: %r", query)
    query_vector = embedder.embed_texts([query], task="search_query")[0]

    client = QdrantClient(url=QDRANT_URL)
    qdrant_filter = _build_filter(filter)

    logger.info(
        "Searching '%s' (top_k=%d, filter=%s)...", COLLECTION_NAME, top_k, filter
    )
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=qdrant_filter,
        limit=top_k,
        with_payload=True,
    )

    hits: List[Dict[str, Any]] = []
    for hit in results:
        payload = hit.payload or {}
        hits.append(
            {
                "score": hit.score,
                "text": payload.get("text", ""),
                "metadata": {k: v for k, v in payload.items() if k != "text"},
            }
        )

    logger.info("Found %d results.", len(hits))
    return hits


def search_with_file_context(
    query: str,
    filter: Optional[Dict[str, Any]] = None,
    top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
    """
    Semantic search **plus** automatic expansion to all sibling chunks.

    Problem it solves
    ─────────────────
    When a source file is split into N chunks, a plain vector search
    only returns whichever individual chunks score highest.  If the
    answer spans multiple chunks (e.g. a hook defined in chunk 0 and
    its helper function in chunk 1), the caller would miss context.

    This function:
      1. Runs a normal semantic search to find the most relevant files.
      2. Uses each hit's ``file_id`` to scroll **all** chunks from that
         file out of Qdrant (regardless of their individual similarity
         scores).
      3. Returns them grouped per file, sorted by ``chunk_index``, so
         the caller always receives the complete source in reading order.

    Return format
    ─────────────
    [
      {
        "file_name":        str,
        "file_path":        str,
        "file_id":          str,
        "file_type":        str,
        "total_chunks":     int,
        "best_match_score": float,      # highest cosine score among hits for this file
        "chunks": [                     # ALL chunks, sorted by chunk_index
          {
            "text":           str,
            "chunk_index":    int,
            "chunk_type":     str,
            "component_name": str,
            "props":          List[str],
            "exports":        List[str],
          },
          ...
        ],
      },
      ...
    ]
    Results are ordered by best_match_score descending.
    """
    hits = search(query, filter, top_k)
    if not hits:
        return []

    # Preserve relevance-ranked order; deduplicate file_ids
    file_scores: Dict[str, float] = {}
    for hit in hits:
        fid = hit["metadata"].get("file_id")
        if fid and fid not in file_scores:
            file_scores[fid] = hit["score"]

    client = QdrantClient(url=QDRANT_URL)
    results: List[Dict[str, Any]] = []

    for file_id, best_score in file_scores.items():
        records, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="file_id", match=MatchValue(value=file_id))]
            ),
            with_payload=True,
            limit=200,  # no file will ever have >200 chunks
        )
        if not records:
            continue

        sorted_chunks = sorted(
            [
                {
                    "text": r.payload.get("text", ""),
                    "chunk_index": r.payload.get("chunk_index", 0),
                    "chunk_type": r.payload.get("chunk_type", ""),
                    "component_name": r.payload.get("component_name", ""),
                    "props": r.payload.get("props", []),
                    "exports": r.payload.get("exports", []),
                }
                for r in records
            ],
            key=lambda x: x["chunk_index"],
        )

        first_payload = records[0].payload or {}
        results.append(
            {
                "file_name": first_payload.get("file_name", ""),
                "file_path": first_payload.get("file_path", ""),
                "file_id": file_id,
                "file_type": first_payload.get("file_type", ""),
                "total_chunks": first_payload.get("total_chunks", len(sorted_chunks)),
                "best_match_score": best_score,
                "chunks": sorted_chunks,
            }
        )

    results.sort(key=lambda x: x["best_match_score"], reverse=True)
    return results
