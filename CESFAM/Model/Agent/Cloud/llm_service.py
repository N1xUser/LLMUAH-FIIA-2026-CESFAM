import os
import sys
import time
import numpy as np
from typing import List, Optional
from models import DocumentChunk, SearchResult
from google import genai
from google.genai import types

class GeminiRAGService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            print("Error: No se encontro API KEY.")
            sys.exit(1)
        self.client = genai.Client(api_key=self.api_key)
        self.embedding_model = "gemini-embedding-2"
        self.generation_model = "gemini-3.6-flash"

    def format_document_for_embedding(self, chunk: DocumentChunk) -> str:
        return f"title: none | text: {chunk.text}"

    def format_query_for_embedding(self, query: str) -> str:
        return f"task: question answering | query: {query}"

    def embed_text(self, text: str) -> np.ndarray:
        response = self.client.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        return np.array(response.embeddings[0].values, dtype=np.float32)

    def embed_chunks_batch(self, chunks: List[DocumentChunk], batch_size: int = 15) -> List[np.ndarray]:
        all_embeddings: List[np.ndarray] = []
        total = len(chunks)

        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]
            formatted_texts = [self.format_document_for_embedding(c) for c in batch]
            success = False
            for attempt in range(3):
                try:
                    response = self.client.models.embed_content(
                        model=self.embedding_model,
                        contents=formatted_texts,
                        config=types.EmbedContentConfig(output_dimensionality=768)
                    )
                    for emb in response.embeddings:
                        all_embeddings.append(np.array(emb.values, dtype=np.float32))
                    success = True
                    break
                except Exception:
                    time.sleep(1.5 ** attempt)
            if not success:
                for item_text in formatted_texts:
                    try:
                        emb = self.embed_text(item_text)
                        all_embeddings.append(emb)
                    except Exception:
                        all_embeddings.append(np.zeros(768, dtype=np.float32))
            print(f"Progreso embeddings: {min(i + batch_size, total)}/{total}", end="\r", flush=True)
        print()
        return all_embeddings

    def generate_answer(self, query: str, context_results: List[SearchResult]) -> str:
        context_snippets = []
        for i, res in enumerate(context_results, 1):
            source_info = f"Documento {i}: [{res.chunk.category}] {res.chunk.relative_path}"
            snippet = f"=== {source_info} ===\n{res.chunk.text}\n"
            context_snippets.append(snippet)
        context_text = "\n".join(context_snippets)
        prompt = f"Basandote en los siguientes documentos:\n\n{context_text}\n\nResponde:\n{query}"
        try:
            response = self.client.models.generate_content(
                model=self.generation_model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            return f"Error al generar respuesta: {e}"
