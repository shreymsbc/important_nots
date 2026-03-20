"""
llm_answer.py
=============
LLM answer layer for the react_toolkit_knowledge RAG system.

Flow:
  User question
       ↓
  search_with_file_context()   — retrieves ALL chunks from relevant files
       ↓
  build_prompt()               — injects retrieved context into prompt
       ↓
  ask_llm()                    — calls gpt-4o and returns detailed answer
       ↓
  Dynamic Q&A loop             — user types questions, type 'exit' to quit

Run:
    cd /home/shreyshah/embedding_testing-master
    python -m db.llm_answer
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI

from db.query import search_with_file_context
from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_K,
    SCORE_THRESHOLD,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(question: str, file_results: List[Dict[str, Any]]) -> str:
    """
    Build the prompt sent to gpt-4o.

    Uses search_with_file_context() results — every relevant file's chunks
    are assembled in reading order so the LLM sees the full component context,
    not just the highest-scoring individual chunk.

    Prompt instructs the LLM to:
      1. Give a clear description of what the component/hook does
      2. List all props with type, required/optional, and description
      3. Show a complete realistic JSX usage example with state and handlers
      4. Cover all variants and optional props
    """
    context_blocks: List[str] = []

    for i, file_result in enumerate(file_results, 1):
        file_name   = file_result["file_name"]
        file_type   = file_result["file_type"]
        best_score  = file_result["best_match_score"]
        chunks      = file_result["chunks"]

        # Assemble all chunks from this file in reading order
        full_text = "\n\n".join(c["text"] for c in chunks)

        # Collect props from all chunks in this file
        all_props = []
        for c in chunks:
            all_props.extend(c.get("props", []))
        props_str = f"  props: {all_props}" if all_props else ""

        context_blocks.append(
            f"[File {i} | {file_name} | type: {file_type} | score: {best_score:.4f}]{props_str}\n"
            f"{full_text}"
        )

    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are an expert React developer assistant for a component library.

Use the retrieved context below to answer the question in full detail.

Your answer MUST include ALL of the following:

1. WHAT it is — clear description of the component or hook (2-3 lines)
2. PROPS TABLE — every prop with its type, required/optional, and description
3. FULL WORKING CODE EXAMPLE — a complete realistic JSX example showing
   the component used inside a parent with state, handlers, and imports
4. VARIANTS / EXTRA USAGE — show different use cases where applicable
   (e.g. different variants, with/without optional props)

Rules:
  - Do NOT copy or repeat the raw context in your answer
  - Do NOT show the internal component definition (const Button = ...)
  - Only show how a DEVELOPER would USE this component in their app
  - Format your answer clearly with sections and code blocks

If the answer is not in the context say:
"I could not find that in the available components."

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""


# ── LLM call ─────────────────────────────────────────────────────────────────

def ask_llm(prompt: str, client: OpenAI) -> str:
    """Send the prompt to gpt-4o and return the answer text."""
    logger.info("Calling %s...", OPENAI_MODEL)
    response = client.chat.completions.create(
        model       = OPENAI_MODEL,
        messages    = [
            {
                "role":    "system",
                "content": (
                    "You are an expert React component library assistant.\n"
                    "When answering:\n"
                    "- Give complete, production-quality code examples\n"
                    "- Show realistic usage with state, handlers, and imports\n"
                    "- Cover all props and variants\n"
                    "- Never show the internal component definition\n"
                    "- Format your answer clearly with sections and code blocks"
                ),
            },
            {
                "role":    "user",
                "content": prompt,
            },
        ],
        temperature = TEMPERATURE,
        max_tokens  = MAX_TOKENS,
    )
    return response.choices[0].message.content.strip()


# ── Full RAG pipeline ─────────────────────────────────────────────────────────

def answer(
    question:    str,
    openai_client: OpenAI,
    filter:      Optional[Dict[str, Any]] = None,
    top_k:       int = TOP_K,
    verbose:     bool = True,
) -> str:
    """
    Full RAG pipeline: question → retrieve → prompt → gpt-4o → answer.

    Args:
        question:       natural language question from the user
        openai_client:  connected OpenAI client
        filter:         optional Qdrant filter dict
                        e.g. {"file_type": "code"} or {"chunk_type": "hook"}
        top_k:          number of files to retrieve
        verbose:        if True, logs retrieved files and scores

    Returns:
        Final answer string from gpt-4o
    """
    logger.info("Question: %r", question)

    # Step 1 — retrieve relevant files with full context
    file_results = search_with_file_context(question, filter=filter, top_k=top_k)

    if not file_results:
        return "No relevant chunks found. Try rephrasing your question."

    # Log what was retrieved
    if verbose:
        logger.info("Retrieved %d file(s):", len(file_results))
        for r in file_results:
            logger.info(
                "  score=%.4f | %s (%d chunk(s))",
                r["best_match_score"],
                r["file_name"],
                len(r["chunks"]),
            )

    # Step 2 — build prompt with full file context
    prompt = build_prompt(question, file_results)

    # Step 3 — call gpt-4o
    return ask_llm(prompt, openai_client)


# ── Dynamic Q&A loop ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  RAG System — React Component Assistant")
    print("  Powered by: Nomic embeddings + gpt-4o")
    print("=" * 60)

    # Connect to OpenAI
    logger.info("Connecting to OpenAI (%s)...", OPENAI_MODEL)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    print("\n  Everything loaded. Type your question below.")
    print("  Type 'exit' to quit.\n")

    while True:
        print("-" * 60)
        question = input("  Your question: ").strip()

        if question.lower() in ("exit", "quit", "q"):
            print("\n  Goodbye!\n")
            break

        if not question:
            print("  Please type a question.")
            continue

        result = answer(question, openai_client)

        print(f"\n  Answer:\n")
        print(f"{result}\n")