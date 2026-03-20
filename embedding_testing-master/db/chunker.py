import re
import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    chunk_id: str
    component_name: str
    chunk_type: str
    chunk_index: int = 0
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    props: List[str] = field(default_factory=list)


def _make_chunk_id(file_path: str, index: int, text: str) -> str:
    """Stable, deterministic SHA-256-based ID (first 16 hex chars)."""
    content = f"{file_path}::{index}::{text}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _determine_chunk_type(name: str, keyword: str) -> str:
    if keyword == "class":
        return "class"
    if name.startswith("use") and len(name) > 3 and name[3].isupper():
        return "hook"
    if name and name[0].isupper():
        return "function_component"
    return "utility"


# ── Tree-sitter based parsing (primary) ──────────────────────────────────────

def _get_js_language():
    from tree_sitter import Language
    import tree_sitter_javascript as tsjs
    return Language(tsjs.language())


def _extract_props(params_node) -> List[str]:
    """Extract prop names from formal_parameters or object_pattern node."""
    if params_node is None:
        return []
    target = params_node
    if params_node.type == "formal_parameters":
        for child in params_node.named_children:
            if child.type == "object_pattern":
                target = child
                break
        else:
            return []
    if target.type != "object_pattern":
        return []
    props: List[str] = []
    for child in target.named_children:
        if child.type == "shorthand_property_identifier_pattern":
            props.append(child.text.decode("utf-8"))
        elif child.type == "object_assignment_pattern":
            # e.g. variant = "primary"  →  first named child is the key
            key = child.named_children[0] if child.named_children else None
            if key and key.type == "shorthand_property_identifier_pattern":
                props.append(key.text.decode("utf-8"))
        elif child.type == "pair_pattern":
            key = child.child_by_field_name("key")
            if key:
                props.append(key.text.decode("utf-8"))
        elif child.type == "rest_pattern":
            for c in child.named_children:
                if c.type == "identifier":
                    props.append(f"...{c.text.decode('utf-8')}")
    return props


def _extract_exports(root) -> List[str]:
    """Collect all exported names from top-level export_statement nodes."""
    exports: List[str] = []
    for node in root.named_children:
        if node.type != "export_statement":
            continue
        for child in node.named_children:
            if child.type == "identifier":
                exports.append(child.text.decode("utf-8"))
            elif child.type in ("function_declaration", "class_declaration"):
                name = child.child_by_field_name("name")
                if name:
                    exports.append(name.text.decode("utf-8"))
            elif child.type in ("lexical_declaration", "variable_declaration"):
                for dc in child.named_children:
                    if dc.type == "variable_declarator":
                        name = dc.child_by_field_name("name")
                        if name:
                            exports.append(name.text.decode("utf-8"))
    return exports


def _iter_top_level_decls(root) -> List[Tuple[int, str, str, List[str]]]:
    """
    Walk the top-level AST children and return
    (start_byte, name, kw, props) for every named declaration.
    Unwraps export_statement wrappers transparently.
    """
    results: List[Tuple[int, str, str, List[str]]] = []

    for node in root.named_children:
        ntype = node.type
        # skip imports, comments, hash-bangs
        if ntype in ("import_statement", "comment", "hash_bang_line"):
            continue

        # unwrap `export const/function/class …`
        actual = node
        if ntype == "export_statement":
            inner = None
            for child in node.named_children:
                if child.type in (
                    "lexical_declaration", "variable_declaration",
                    "function_declaration", "class_declaration",
                ):
                    inner = child
                    break
            if inner is None:
                # plain `export default X;` or `export { X }` — not a new chunk
                continue
            actual = inner

        atype = actual.type

        if atype in ("lexical_declaration", "variable_declaration"):
            for child in actual.named_children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    value_node = child.child_by_field_name("value")
                    if name_node:
                        name = name_node.text.decode("utf-8")
                        is_func = (
                            value_node is not None
                            and value_node.type in ("arrow_function", "function_expression")
                        )
                        kw = "function" if is_func else "variable"
                        props: List[str] = []
                        if value_node and value_node.type == "arrow_function":
                            params = (
                                value_node.child_by_field_name("parameters")
                                or value_node.child_by_field_name("parameter")
                            )
                            props = _extract_props(params)
                        results.append((node.start_byte, name, kw, props))
                    break  # only process the first declarator

        elif atype == "function_declaration":
            name_node = actual.child_by_field_name("name")
            if name_node:
                params = actual.child_by_field_name("parameters")
                results.append((
                    node.start_byte,
                    name_node.text.decode("utf-8"),
                    "function",
                    _extract_props(params),
                ))

        elif atype == "class_declaration":
            name_node = actual.child_by_field_name("name")
            if name_node:
                results.append((node.start_byte, name_node.text.decode("utf-8"), "class", []))

    return results


def _ts_chunk_react(source: str, file_stem: str, file_path: str) -> List[Chunk]:
    """AST-accurate semantic chunking via tree-sitter."""
    from tree_sitter import Parser

    parser = Parser(_get_js_language())
    tree = parser.parse(source.encode())
    root = tree.root_node

    import_texts: List[str] = [
        source[n.start_byte : n.end_byte]
        for n in root.named_children
        if n.type == "import_statement"
    ]
    all_exports = _extract_exports(root)
    declarations = _iter_top_level_decls(root)

    if not declarations:
        chunk_id = _make_chunk_id(file_path, 0, source)
        return [
            Chunk(
                text=source.strip(),
                chunk_id=chunk_id,
                component_name=file_stem,
                chunk_type="module",
                chunk_index=0,
                imports=import_texts,
                exports=all_exports,
            )
        ]

    import_prefix = "\n".join(import_texts) + "\n\n" if import_texts else ""
    # preamble = everything before the first declaration (file comment + imports)
    preamble_text = source[: declarations[0][0]].rstrip()

    chunks: List[Chunk] = []
    for i, (start, name, kw, props) in enumerate(declarations):
        seg_end = declarations[i + 1][0] if i + 1 < len(declarations) else len(source)
        segment = source[start:seg_end].strip()
        if not segment:
            continue
        if i == 0:
            # First chunk: prepend full preamble (comment + imports) for context
            if preamble_text:
                segment = preamble_text + "\n\n" + segment
        else:
            # Subsequent chunks: prepend imports only so chunk is self-contained
            if import_prefix:
                segment = import_prefix + segment

        chunk_type = _determine_chunk_type(name, kw)
        chunk_id = _make_chunk_id(file_path, i, segment)
        chunks.append(
            Chunk(
                text=segment,
                chunk_id=chunk_id,
                component_name=name,
                chunk_type=chunk_type,
                chunk_index=i,
                imports=import_texts,
                exports=[name] if name in all_exports else [],
                props=props,
            )
        )

    return chunks or [
        Chunk(
            text=source.strip(),
            chunk_id=_make_chunk_id(file_path, 0, source),
            component_name=file_stem,
            chunk_type="module",
            chunk_index=0,
            imports=import_texts,
            exports=all_exports,
        )
    ]


# ── Regex fallback (used when tree-sitter unavailable) ───────────────────────

_TOP_LEVEL_RE = re.compile(
    r"^(?:export\s+(?:default\s+)?)?(?P<kw>const|let|var|function|class)\s+"
    r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)",
    re.MULTILINE,
)


def _regex_chunk_react(source: str, file_stem: str, file_path: str) -> List[Chunk]:
    """Fallback: regex-based chunking when tree-sitter is unavailable."""
    boundaries: List[Tuple[int, str, str]] = []
    for m in _TOP_LEVEL_RE.finditer(source):
        line_start = source.rfind("\n", 0, m.start()) + 1
        if m.start() - line_start != 0:
            continue
        if source[line_start:].lstrip().startswith("import"):
            continue
        boundaries.append((m.start(), m.group("name"), m.group("kw")))

    if not boundaries:
        chunk_id = _make_chunk_id(file_path, 0, source)
        return [
            Chunk(
                text=source.strip(),
                chunk_id=chunk_id,
                component_name=file_stem,
                chunk_type="module",
                chunk_index=0,
            )
        ]

    preamble = source[: boundaries[0][0]]
    chunks: List[Chunk] = []
    for i, (start, name, kw) in enumerate(boundaries):
        seg_end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(source)
        segment = source[start:seg_end].strip()
        if not segment:
            continue
        if i == 0 and preamble.strip():
            segment = preamble.rstrip() + "\n\n" + segment
        chunk_type = _determine_chunk_type(name, kw)
        chunk_id = _make_chunk_id(file_path, i, segment)
        chunks.append(
            Chunk(
                text=segment,
                chunk_id=chunk_id,
                component_name=name,
                chunk_type=chunk_type,
                chunk_index=i,
            )
        )

    return chunks or [
        Chunk(
            text=source.strip(),
            chunk_id=_make_chunk_id(file_path, 0, source),
            component_name=file_stem,
            chunk_type="module",
            chunk_index=0,
        )
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def chunk_react_file(file_path: str) -> List[Chunk]:
    """Chunk a React/JS/TS file.  Uses tree-sitter AST; falls back to regex."""
    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to read %s: %s", file_path, exc)
        return []
    try:
        chunks = _ts_chunk_react(source, path.stem, file_path)
        logger.debug("tree-sitter chunked %s → %d chunks", path.name, len(chunks))
        return chunks
    except Exception as exc:
        logger.warning(
            "tree-sitter failed for %s (%s); falling back to regex.", path.name, exc
        )
        return _regex_chunk_react(source, path.stem, file_path)


_HEADING_RE = re.compile(r"^(#{1,3}\s+.+)$", re.MULTILINE)
_MAX_CHARS: int = 2800  # ≈700 tokens @ 4 chars/token


def chunk_markdown_file(file_path: str) -> List[Chunk]:
    """Split a Markdown file by H1/H2/H3 headings into bounded chunks."""
    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to read %s: %s", file_path, exc)
        return []

    file_stem = path.stem
    positions = [m.start() for m in _HEADING_RE.finditer(source)]

    if not positions:
        chunk_id = _make_chunk_id(file_path, 0, source)
        return [
            Chunk(
                text=source.strip(),
                chunk_id=chunk_id,
                component_name=file_stem,
                chunk_type="section",
                chunk_index=0,
            )
        ]

    chunks: List[Chunk] = []
    for i, start in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(source)
        text = source[start:end].strip()
        if not text:
            continue
        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS]
        heading_line = text.split("\n")[0]
        m = re.match(r"^#{1,3}\s+(.+)$", heading_line)
        section_name = m.group(1).strip() if m else file_stem
        chunk_id = _make_chunk_id(file_path, i, text)
        chunks.append(
            Chunk(
                text=text,
                chunk_id=chunk_id,
                component_name=section_name,
                chunk_type="section",
                chunk_index=i,
            )
        )

    return chunks
