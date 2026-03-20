from dataclasses import dataclass, asdict, field
from typing import List, Literal

from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "react_toolkit_knowledge"
VECTOR_SIZE = 768
DISTANCE = Distance.COSINE


def get_vector_config() -> VectorParams:
    """Return Qdrant VectorParams for the collection (size=768, cosine)."""
    return VectorParams(size=VECTOR_SIZE, distance=DISTANCE)


@dataclass
class ChunkMetadata:
    """
    Deterministic payload stored alongside every Qdrant vector.

    Key design goals
    ────────────────
    file_id       — SHA-256 of the *full* file content.  Stable as long as the
                    file does not change.  Allows fetching ALL sibling chunks
                    from the same file in a single Qdrant scroll call.

    chunk_index   — 0-based position of this chunk within its source file.
                    Together with total_chunks it lets a caller reconstruct the
                    original reading order.

    total_chunks  — How many chunks the file was split into.  A value of 1
                    means the whole file is a single chunk.

    props         — Extracted React prop names (components / hooks only).
                    Useful for filtering: "find components that accept an
                    onClick prop".

    imports       — List of raw import statement strings from the source file.
                    Tells the model (and human reader) what libraries/components
                    this chunk depends on.

    exports       — Names exported by this specific chunk.
    """

    file_name: str
    file_path: str
    file_id: str                             # SHA-256 of full file content
    file_type: Literal["code", "markdown"]
    language: Literal["javascript", "typescript", "markdown"]
    component_name: str
    chunk_id: str
    chunk_type: str
    chunk_index: int                         # 0-based position within file
    total_chunks: int                        # total chunks from this file
    source: Literal["codes", "markdown_files"]
    props: List[str] = field(default_factory=list)    # React prop names
    imports: List[str] = field(default_factory=list)  # raw import strings
    exports: List[str] = field(default_factory=list)  # exported identifiers

    def to_dict(self) -> dict:
        return asdict(self)
