from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class DocumentChunk:
    chunk_id: str
    source_file: str
    relative_path: str
    category: str
    text: str
    embedding: Optional[np.ndarray] = None

@dataclass
class SearchResult:
    chunk: DocumentChunk
    similarity: float
