from fastapi import Request, HTTPException
import hmac
import hashlib
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def validate_meta_signature(request: Request):
    """
    FastAPI dependency to validate that a request actually came from Meta.
    Verifies the X-Hub-Signature-256 header.
    """
    if not settings.VERIFY_META_SIGNATURE:
        return True

    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header")
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # Prefix usually looks like 'sha256=...'
    try:
        _, signature = signature_header.split('=', 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature format")

    body = await request.body()
    
    expected_signature = hmac.new(
        settings.META_APP_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        logger.warning(f"Invalid Meta signature. Expected {expected_signature}, got {signature}")
        raise HTTPException(status_code=400, detail="Invalid Meta signature")
    
    return True

class MetaHandler:
    @staticmethod
    async def parse_message(request: Request) -> dict:
        """
        Extract key details from the Meta webhook request payload.
        Handles nested JSON structure and different message types.
        """
        try:
            payload = await request.json()
            
            # Check if this is a message status update (delivered, read, etc.)
            # or an actual message
            entry = payload.get("entry", [])[0]
            change = entry.get("changes", [])[0]
            value = change.get("value", {})
            
            # If it's just a status update, we can ignore it or process it differently
            status = value.get("statuses")
            if status:
                return {
                    "is_status": True,
                    "status_info": status[0]
                }
            
            messages = value.get("messages", [])
            if not messages:
                return {"is_valid": False}
                
            msg = messages[0]
            contact = value.get("contacts", [])[0]
            
            from_number = contact.get("wa_id")
            message_type = msg.get("type")
            message_id = msg.get("id")
            
            body = ""
            media_id = None
            mime_type = None
            button_id = None
            if message_type == "text":
                body = msg.get("text", {}).get("body", "")
            elif message_type == "image":
                body = msg.get("image", {}).get("caption", "")
                media_id = msg.get("image", {}).get("id")
                mime_type = msg.get("image", {}).get("mime_type")
            elif message_type in ["audio", "voice"]:
                audio_data = msg.get(message_type, {})
                media_id = audio_data.get("id")
                mime_type = audio_data.get("mime_type")
                body = "[Voice/Audio Message]"
            elif message_type == "interactive":
                interactive = msg.get("interactive", {})
                itype = interactive.get("type")
                if itype == "button_reply":
                    btn = interactive.get("button_reply", {})
                    body = btn.get("title", "")
                    button_id = btn.get("id", "")  # carries snooze/done prefix
                elif itype == "list_reply":
                    lr = interactive.get("list_reply", {})
                    body = lr.get("title", "")
                    button_id = lr.get("id", "")
                else:
                    body = str(interactive)

            return {
                "is_valid": True,
                "is_status": False,
                "from_number": from_number,
                "message_type": message_type,
                "body": body,
                "button_id": button_id,
                "media_id": media_id,
                "mime_type": mime_type,
                "message_id": message_id
            }
            
        except Exception as e:
            logger.error(f"Error parsing Meta payload: {str(e)}")
            return {
                "is_valid": False,
                "error": str(e)
            }
