import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class WhatsAppSender:
    def __init__(self):
        self.access_token = settings.META_ACCESS_TOKEN
        self.phone_number_id = settings.META_PHONE_NUMBER_ID
        self.base_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def send_message(self, to_number: str, message: str) -> bool:
        """
        Send a WhatsApp text message via Meta Cloud API.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code in (200, 201):
                    logger.info(f"Sent message to {to_number}")
                    return True
                else:
                    logger.error(f"Error sending Meta WhatsApp message to {to_number}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False

    async def send_interactive_buttons(self, to_number: str, body_text: str, buttons: list[dict]) -> bool:
        """
        Send a WhatsApp interactive button message (max 3 buttons).
        buttons = [{"id": "btn_1", "title": "Yes"}, ...]
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"][:20]}}
                        for btn in buttons[:3]
                    ]
                }
            }
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(self.base_url, headers=self.headers, json=payload, timeout=10.0)
                if res.status_code in (200, 201):
                    return True
                logger.error(f"Error sending buttons to {to_number}: {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending interactive buttons: {e}")
            return False

    async def send_interactive_list(self, to_number: str, body_text: str, button_label: str, sections: list[dict]) -> bool:
        """
        Send a WhatsApp interactive list message.
        sections = [{"title": "Options", "rows": [{"id": "opt_1", "title": "Formal", "description": "..."}]}]
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body_text},
                "action": {
                    "button": button_label[:20],
                    "sections": sections
                }
            }
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(self.base_url, headers=self.headers, json=payload, timeout=10.0)
                if res.status_code in (200, 201):
                    return True
                logger.error(f"Error sending list to {to_number}: {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending interactive list: {e}")
            return False

    async def download_media(self, media_id: str) -> bytes | None:
        try:
            async with httpx.AsyncClient() as client:
                media_url_res = await client.get(
                    f"https://graph.facebook.com/v19.0/{media_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                if media_url_res.status_code != 200:
                    logger.error(f"Failed to get media URL: {media_url_res.text}")
                    return None
                
                media_url = media_url_res.json().get("url")
                media_res = await client.get(
                    media_url,
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                if media_res.status_code == 200:
                    return media_res.content
                else:
                    logger.error(f"Failed to download media bytes: {media_res.text}")
                    return None
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None

whatsapp_sender = WhatsAppSender()
