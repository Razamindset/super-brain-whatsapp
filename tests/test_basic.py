import pytest
import asyncio
from app.database.sqlite_impl import SQLiteDatabase
from app.config import settings
import os

@pytest.mark.asyncio
async def test_database_operations():
    # Use a test database
    test_db_url = "sqlite+aiosqlite:///./test_assistant.db"
    db = SQLiteDatabase(test_db_url)
    await db.initialize()
    
    user_id = "whatsapp:+123456789"
    message = "Hello AI"
    response = "Hello User"
    
    # Test saving conversation
    await db.save_conversation(user_id, message, response, "test-model")
    
    # Test getting history
    history = await db.get_conversation_history(user_id)
    assert len(history) > 0
    assert history[-1]["message"] == message
    assert history[-1]["response"] == response
    
    # Test document storage
    await db.save_document(user_id, "This is a secret note", "doc-123")
    user = await db.get_user_metadata(user_id)
    assert user["id"] == user_id
    
    # Cleanup
    await db.engine.dispose()
    if os.path.exists("./test_assistant.db"):
        os.remove("./test_assistant.db")

def test_config_loading():
    assert settings.DATABASE_URL is not None
    assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]
