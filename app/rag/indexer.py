from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings
import logging
import logging

logger = logging.getLogger(__name__)

class RAGIndexer:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY
        )

    async def get_embedding(self, text: str) -> list[float]:
        """
        Embed a piece of text to push natively into Supabase vector lists.
        """
        try:
            return await self.embeddings.aembed_query(text)
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return []

indexer = RAGIndexer()
