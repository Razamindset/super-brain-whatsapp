from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY
        )

    async def query(self, query_text: str, user_id: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for a query, returning dicts with 'id' and 'document_text'.
        The id is needed so the LLM can flag conflicting memories for deletion.
        """
        try:
            from app.database.supabase_impl import db
            vector = await self.embeddings.aembed_query(query_text)
            if vector:
                results = await db.match_memories(vector, match_threshold=0.7, match_count=k, user_id=user_id)
                return results
            return []
        except Exception as e:
            logger.error(f"Error querying PGVector RPC engine: {str(e)}")
            return []

engine = RAGEngine()
