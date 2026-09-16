import argparse
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv

from models import SearchResult
from chunker import MarkdownChunker
from vector_store import VectorStore
from llm_service import GeminiRAGService

load_dotenv()

class RAGAgent:
    def __init__(self):
        base_script_dir = Path(__file__).resolve().parent
        self.process_dir = base_script_dir / "Process"
        self.cache_file = base_script_dir / "cache" / "embeddings_store.pkl"
        self.chunker = MarkdownChunker()
        self.vector_store = VectorStore(self.cache_file)
        self.service = GeminiRAGService()

    def index_documents(self):
        if not self.process_dir.exists():
            print(f"La carpeta no existe: {self.process_dir}")
            return
        md_files = list(self.process_dir.rglob("*.md"))
        files_to_process = [f for f in md_files if not self.vector_store.is_file_up_to_date(f)]
        if not files_to_process:
            return
        processed_file_paths = {str(p.resolve()) for p in files_to_process}
        if self.vector_store.chunks:
            self.vector_store.chunks = [
                c for c in self.vector_store.chunks
                if str(Path(c.source_file).resolve()) not in processed_file_paths
            ]
        new_chunks = []
        for file_path in files_to_process:
            new_chunks.extend(self.chunker.chunk_document(file_path, self.process_dir))
        if new_chunks:
            embeddings = self.service.embed_chunks_batch(new_chunks, batch_size=15)
            for chunk, emb in zip(new_chunks, embeddings):
                chunk.embedding = emb
            self.vector_store.chunks.extend(new_chunks)
            for file_path in files_to_process:
                self.vector_store.update_file_hash(file_path)
            self.vector_store.save()

    def query(self, user_question: str, top_k: int = 5):
        if not self.vector_store.chunks:
            self.index_documents()
        formatted_query = self.service.format_query_for_embedding(user_question)
        query_emb = self.service.embed_text(formatted_query)
        search_results = self.vector_store.search(query_emb, top_k=top_k)
        answer_generator = self.service.generate_answer(user_question, search_results)
        return answer_generator, search_results

def main():
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str)
    args = parser.parse_args()

    agent = RAGAgent()
    agent.index_documents()
    answer_generator, results = agent.query(args.query)

    for chunk in answer_generator:
        print(chunk, end="", flush=True)
    print("\n", flush=True)

if __name__ == "__main__":
    main()
