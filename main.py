import logging
from fastapi import FastAPI, Request, BackgroundTasks, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.whatsapp.handler import validate_meta_signature, MetaHandler
from app.whatsapp.sender import whatsapp_sender
from app.conversation.manager import manager
from app.database.supabase_impl import db
from app.config import settings
from app.scheduler.engine import scheduler_engine

import sys
import io

# Force UTF-8 encoding for Windows consoles to handle emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("assistant.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Super Brain")

# Mount public directory for static assets
app.mount("/static", StaticFiles(directory="public"), name="static")

@app.on_event("startup")
async def startup_event():
    # Initialize database tables
    await db.initialize()
    scheduler_engine.start()
    await scheduler_engine.load_reminders()
    logger.info("Application started and database initialized.")

@app.get("/")
async def root():
    return FileResponse("public/index.html")

@app.get("/privacy-policy")
async def privacy_policy():
    return FileResponse("public/privacy.html")

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """
    Meta Webhook Verification endpoint.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == settings.META_WEBHOOK_VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            return Response(content=challenge, status_code=200)
        else:
            return Response(status_code=403)
    return Response(status_code=400)


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    _validated: bool = Depends(validate_meta_signature)
):
    """
    Meta Webhook endpoint for incoming WhatsApp messages.
    """
    try:
        # Parse the message details
        msg_data = await MetaHandler.parse_message(request)
        
        if msg_data.get("is_status"):
            # Ignore delivery/read statuses
            return {"status": "accepted"}
            
        if not msg_data.get("is_valid"):
            return {"status": "ignored"}
            
        from_number = msg_data.get("from_number")
        message_type = msg_data.get("message_type")
        
        # Fallback for unsupported types
        if message_type not in ["text", "image", "interactive"]:
            fallback_msg = f"{message_type.capitalize()}s not supported now. Please send a text or image message."
            background_tasks.add_task(whatsapp_sender.send_message, from_number, fallback_msg)
            return {"status": "accepted"}
            
        body = msg_data.get("body", "")
        media_id = msg_data.get("media_id")
        button_id = msg_data.get("button_id")
        logger.info(f"Received {message_type} message from {from_number}: {body[:50]}...")
        
        # Process the message in the background
        background_tasks.add_task(manager.handle_message, from_number, body, media_id, button_id)
        
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return {"status": "error", "detail": str(e)}

@app.get("/admin")
async def admin_dashboard():
    return FileResponse("public/admin.html")

@app.get("/api/admin/stats")
async def api_admin_stats():
    return await db.get_stats()

@app.get("/api/admin/conversations")
async def api_admin_conversations():
    return {"conversations": await db.get_all_conversations()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
