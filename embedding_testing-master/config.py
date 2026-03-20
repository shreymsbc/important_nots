"""
config.py
=========
Central configuration for the react_toolkit_knowledge RAG system.

IMPORTANT:
  - Never push this file to GitHub
  - Add config.py to your .gitignore
  - Never share this file with anyone
"""

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str  = "abcd-xyz-pqr"   # ← replace with your real key
OPENAI_MODEL:   str  = "gpt-4.1-mini"
MAX_TOKENS:     int  = 1500
TEMPERATURE:    float = 0.2

# ── Qdrant ────────────────────────────────────────────────────────────────────
QDRANT_URL:      str = "http://localhost:6333"
COLLECTION_NAME: str = "react_toolkit_knowledge"

# ── Embedding model ───────────────────────────────────────────────────────────
EMBED_MODEL:     str   = "nomic-ai/nomic-embed-text-v1.5"
VECTOR_SIZE:     int   = 768
TOP_K:           int   = 5
SCORE_THRESHOLD: float = 0.3