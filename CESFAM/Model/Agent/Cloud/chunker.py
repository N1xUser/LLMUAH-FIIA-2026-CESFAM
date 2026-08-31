from pathlib import Path
from typing import List
from models import DocumentChunk

class MarkdownChunker:
    def __init__(self, target_chunk_size: int = 1200):
        self.target_chunk_size = target_chunk_size

    def chunk_document(self, file_path: Path, base_dir: Path) -> List[DocumentChunk]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_content = f.read()
        except Exception as e:
            print(f"Error al leer {file_path}: {e}")
            return []

        rel_path = file_path.relative_to(base_dir).as_posix()
        parts = rel_path.split("/")
        category = parts[0] if len(parts) > 1 else "General"

        paragraphs = raw_content.split("\n\n")
        chunks = []
        current_text = ""
        chunk_idx = 0

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if len(current_text) + len(p) > self.target_chunk_size and current_text:
                chunks.append(DocumentChunk(
                    chunk_id=f"{rel_path}_{chunk_idx}",
                    source_file=str(file_path),
                    relative_path=rel_path,
                    category=category,
                    text=current_text.strip()
                ))
                chunk_idx += 1
                current_text = p
            else:
                current_text = f"{current_text}\n\n{p}".strip() if current_text else p

        if current_text:
            chunks.append(DocumentChunk(
                chunk_id=f"{rel_path}_{chunk_idx}",
                source_file=str(file_path),
                relative_path=rel_path,
                category=category,
                text=current_text.strip()
            ))

        return chunks
