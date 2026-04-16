from supabase import create_client, Client
from app.config import settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SupabaseDatabase:
    def __init__(self):
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    async def initialize(self):
        logger.info("Supabase connection hooked successfully.")

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.supabase.table("users").select("*").eq("id", user_id).single().execute()
            return res.data
        except Exception:
            return None

    async def ensure_user(self, user_id: str) -> Dict[str, Any]:
        """Upsert user row and return it."""
        self.supabase.table("users").upsert({"id": user_id}, on_conflict="id").execute()
        return await self.get_user(user_id)

    async def update_user_onboarding(self, user_id: str, updates: Dict[str, Any]):
        try:
            self.supabase.table("users").update(updates).eq("id", user_id).execute()
        except Exception as e:
            logger.error(f"Error updating user onboarding: {e}")

    async def save_conversation(self, user_id: str, message: str, response: str, model_used: str):
        try:
            self.supabase.table("users").upsert({"id": user_id}).execute()
            self.supabase.table("conversations").insert({
                "user_id": user_id,
                "message": message,
                "response": response,
                "model_used": model_used
            }).execute()
        except Exception as e:
            logger.error(f"Error saving to Supabase: {e}")

    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            res = self.supabase.table("conversations").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(limit).execute()
            conversations = res.data
            return [{"message": c["message"], "response": c["response"], "timestamp": c["timestamp"]} for c in reversed(conversations)]
        except Exception as e:
            logger.error(f"Error getting history from Supabase: {e}")
            return []

    async def save_document(self, user_id: str, document_text: str, doc_id: str, embedding: List[float]):
        try:
            self.supabase.table("users").upsert({"id": user_id}).execute()
            self.supabase.table("memories").insert({
                "id": doc_id,
                "user_id": user_id,
                "document_text": document_text,
                "embedding": embedding
            }).execute()
            logger.info(f"Supabase saved memory {doc_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving memory to Supabase: {e}")

    async def get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Return all memory rows (id + document_text) for a user."""
        try:
            res = self.supabase.table("memories").select("id, document_text").eq("user_id", user_id).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching memories for {user_id}: {e}")
            return []

    async def delete_memory(self, doc_id: str) -> bool:
        """Delete a single memory row by its UUID."""
        try:
            self.supabase.table("memories").delete().eq("id", doc_id).execute()
            logger.info(f"Deleted memory {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory {doc_id}: {e}")
            return False

    async def match_memories(self, query_embedding: List[float], match_threshold: float, match_count: int, user_id: str) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts with 'id' and 'document_text' for matched memories.
        Returning ids allows the LLM to reference them for conflict resolution / deletion.
        """
        try:
            res = self.supabase.rpc("match_memories", {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "p_user_id": user_id
            }).execute()
            return [{"id": doc["id"], "document_text": doc["document_text"]} for doc in res.data]
        except Exception as e:
            logger.error(f"Error matching memories in Supabase: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        try:
            users_res = self.supabase.table("users").select("id", count="exact").execute()
            convs_res = self.supabase.table("conversations").select("id", count="exact").execute()
            docs_res = self.supabase.table("memories").select("id", count="exact").execute()
            return {
                "users": users_res.count or 0,
                "conversations": convs_res.count or 0,
                "memories": docs_res.count or 0
            }
        except Exception as e:
            logger.error(f"Error getting stats from Supabase: {e}")
            return {"users": 0, "conversations": 0, "memories": 0}

    async def get_all_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            res = self.supabase.table("conversations").select("*").order("timestamp", desc=True).limit(limit).execute()
            return res.data
        except Exception as e:
            logger.error(f"Error getting all conversations: {e}")
            return []

db = SupabaseDatabase()
