import hashlib
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from models import DocumentChunk, SearchResult

class VectorStore:
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.chunks: List[DocumentChunk] = []
        self.file_hashes: Dict[str, str] = {}
        self.matrix: Optional[np.ndarray] = None
        self.load()

    def _compute_file_hash(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def is_file_up_to_date(self, file_path: Path) -> bool:
        key = str(file_path.resolve())
        if key not in self.file_hashes:
            return False
        return self.file_hashes[key] == self._compute_file_hash(file_path)

    def update_file_hash(self, file_path: Path):
        key = str(file_path.resolve())
        self.file_hashes[key] = self._compute_file_hash(file_path)

    def save(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "chunks": self.chunks,
            "file_hashes": self.file_hashes,
        }
        with open(self.cache_file, "wb") as f:
            pickle.dump(data, f)
        self._build_matrix()

    def load(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data.get("chunks", [])
                    self.file_hashes = data.get("file_hashes", {})
                self._build_matrix()
            except Exception as e:
                print(f"Error al cargar cache: {e}")
                self.chunks = []
                self.file_hashes = {}

    def _build_matrix(self):
        valid = [c.embedding for c in self.chunks if c.embedding is not None]
        if valid:
            self.matrix = np.vstack(valid)
        else:
            self.matrix = None

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[SearchResult]:
        if self.matrix is None or len(self.chunks) == 0:
            return []

        q_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        doc_norms = self.matrix / (np.linalg.norm(self.matrix, axis=1, keepdims=True) + 1e-10)
        similarities = np.dot(doc_norms, q_norm)

        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append(SearchResult(
                chunk=self.chunks[idx],
                similarity=float(similarities[idx])
            ))
        return results
