"""Document Parser and Semantic Chunker for FinMate Financial Knowledge Base."""

import os
import re
from typing import Dict, List, Any, Tuple


Tuple_Dict = Tuple[Dict[str, Any], str]


def parse_markdown_metadata(content: str) -> Tuple[Dict[str, Any], str]:
    """Extracts metadata headers from markdown documents."""
    meta = {
        "title": "Financial Guidance Document",
        "organization": "Official Financial Authority",
        "reference_code": "GEN-001",
        "publication_date": "2025-01-01",
        "topic": "Personal Finance",
        "jurisdiction": "India"
    }

    lines = content.splitlines()
    body_lines = []
    in_meta_block = False

    for line in lines:
        if "**Document Metadata**:" in line:
            in_meta_block = True
            continue
        if in_meta_block:
            if line.startswith("---"):
                in_meta_block = False
                continue
            m = re.match(r"-\s+\*\*([^*]+)\*\*:\s*(.*)", line.strip())
            if m:
                key = m.group(1).lower().replace(" ", "_")
                val = m.group(2).strip()
                meta[key] = val
        else:
            body_lines.append(line)

    return meta, "\n".join(body_lines)


def chunk_document(
    filepath: str,
    target_chunk_size: int = 600
) -> List[Dict[str, Any]]:
    """Splits a financial knowledge document into semantic chunks with metadata."""
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    meta, body = parse_markdown_metadata(content)

    # Split on markdown headings (## or ###)
    sections = re.split(r"\n(?=#{2,3}\s+)", body)
    chunks = []
    chunk_index = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract section header if present
        header_match = re.match(r"(#{2,3}\s+[^\n]+)", section)
        header = header_match.group(1).strip("# ") if header_match else "General Guidance"

        # Split into paragraphs
        paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
        current_chunk_text = ""

        for p in paragraphs:
            if len(current_chunk_text) + len(p) < target_chunk_size:
                current_chunk_text += ("\n\n" if current_chunk_text else "") + p
            else:
                if current_chunk_text:
                    chunk_index += 1
                    chunks.append({
                        "chunk_id": f"{filename}::chunk_{chunk_index}",
                        "document_name": filename,
                        "title": meta.get("title", filename),
                        "organization": meta.get("organization", "Financial Regulatory Body"),
                        "reference_code": meta.get("reference_code", "REF-NA"),
                        "topic": meta.get("topic", "General Finance"),
                        "jurisdiction": meta.get("jurisdiction", "India"),
                        "section_header": header,
                        "text": current_chunk_text.strip()
                    })
                current_chunk_text = p

        if current_chunk_text:
            chunk_index += 1
            chunks.append({
                "chunk_id": f"{filename}::chunk_{chunk_index}",
                "document_name": filename,
                "title": meta.get("title", filename),
                "organization": meta.get("organization", "Financial Regulatory Body"),
                "reference_code": meta.get("reference_code", "REF-NA"),
                "topic": meta.get("topic", "General Finance"),
                "jurisdiction": meta.get("jurisdiction", "India"),
                "section_header": header,
                "text": current_chunk_text.strip()
            })

    return chunks


def load_knowledge_base_chunks(knowledge_dir: str) -> List[Dict[str, Any]]:
    """Loads and chunks all markdown documents in the knowledge directory."""
    all_chunks = []
    for fname in sorted(os.listdir(knowledge_dir)):
        if fname.endswith(".md"):
            fpath = os.path.join(knowledge_dir, fname)
            chunks = chunk_document(fpath)
            all_chunks.extend(chunks)
    return all_chunks
