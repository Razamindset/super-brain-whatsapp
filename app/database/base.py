from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

class Database(ABC):
    @abstractmethod
    async def initialize(self):
        """Initialize database tables and schema."""
        pass

    @abstractmethod
    async def save_conversation(self, user_id: str, message: str, response: str, model_used: str):
        """Save a conversation turn to history."""
        pass

    @abstractmethod
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve last N messages for a user."""
        pass

    @abstractmethod
    async def save_document(self, user_id: str, document_text: str, doc_id: str):
        """Save a user document/note reference."""
        pass

    @abstractmethod
    async def get_user_metadata(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific user."""
        pass
