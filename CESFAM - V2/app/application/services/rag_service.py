import sys
import os
from pathlib import Path


cesfam_agent_path = str(Path(__file__).resolve().parent.parent.parent.parent.parent / "CESFAM - Pipeline" / "Model" / "Agent" / "Cloud")
if cesfam_agent_path not in sys.path:
    sys.path.append(cesfam_agent_path)

try:
    from agent import RAGAgent
except ImportError:
    RAGAgent = None

from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.application.interfaces.llm_provider import LLMProvider
from app.domain.entities.message import Message, MessageRole
from app.domain.repositories.vector_repository import VectorRepository

class RAGService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_repository: VectorRepository,
        llm_provider: LLMProvider,
        top_k: int = 5,
    ) -> None:
        self._top_k = top_k
        if RAGAgent:
            self._agent = RAGAgent()
        else:
            self._agent = None

    async def answer(self, query: str, history: list[Message] | None = None) -> str:
        if not self._agent:
            return "El agente RAG de CESFAM no pudo ser cargado."
        
        
        
        answer_generator, search_results = self._agent.query(query, top_k=self._top_k)
        
        
        full_answer = ""
        for chunk in answer_generator:
            full_answer += chunk
            
        return full_answer
