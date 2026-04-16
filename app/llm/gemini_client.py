from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import base64

logger = logging.getLogger(__name__)

class ReminderData(BaseModel):
    time: str = Field(description="The exact ISO 8601 formatted datetime string of when the reminder should trigger (e.g., '2023-10-25T14:30:00+05:00'). Convert any requested times (like 'in 5 minutes') to an absolute timestamp string based on the user's provided local timezone.")
    text: str = Field(description="The short text message to send to the user when the reminder triggers.")

class AssistantAction(BaseModel):
    reply: str = Field(description="The direct text reply to the user. Use ONLY WhatsApp markdown syntax (*bold*, _italic_, ~strikethrough~). Do NOT use standard markdown headers, lists, or **.")
    memory_to_save: Optional[str] = Field(None, description="A single factual statement, preference, or operational rule to index for long-term memory if the user shares something important to remember (e.g. 'User has a dog named Rex', 'Use emojis from now on', 'I am allergic to peanuts'). Must be Null if nothing important to save.")
    memory_ids_to_delete: Optional[List[str]] = Field(None, description="A list of memory UUIDs (from the 'Existing relevant memories' context provided to you) that are now OUTDATED or CONTRADICTED by the new memory you are saving. For example, if saving 'Do not use emojis', you must delete any old memory like 'Use emojis from now on'. Only populate when memory_to_save is also set and old conflicting memories exist in context.")
    reminders: Optional[List[ReminderData]] = Field(None, description="A list of reminders to schedule for the user, if perfectly requested.")
    list_reminders: bool = Field(False, description="Set to true if the user explicitly asks to see their reminders or check what they have scheduled.")
    cancel_reminder_id: Optional[str] = Field(None, description="The UUID of a reminder to cancel, if the user explicitly asks to remove or cancel a specific reminder from their list. Get the ID from the 'Pending Reminders' context provided to you.")
    interactive_widget: Optional[Dict[str, Any]] = Field(None, description="Use this to counter-ask or clarify utilizing WhatsApp interactive tools instead of plain text. Formats: {'type': 'button', 'options': ['Ans 1', 'Ans 2']} OR {'type': 'list', 'button_label': 'Select', 'sections': [{'title': 'Options', 'rows': [{'id': 'opt1', 'title': 'First'}, {'id': 'opt2', 'title': 'Second'}]}]}. Max 3 buttons or 10 list items.")

class GeminiClient:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        self.structured_llm = self.llm.with_structured_output(AssistantAction)

    async def get_response(self, system_instruction: str, history: List[Dict[str, Any]], user_message: str, image_bytes: bytes = None) -> AssistantAction:
        """
        Generate an AssistantAction response from Gemini using system instructions, conversation history, and the current message/image.
        """
        # Formulate messages for LangChain ChatModel
        messages = [
            ("system", system_instruction)
        ]
        
        # Add history
        for turn in history:
            messages.append(("human", turn["message"]))
            messages.append(("ai", turn["response"]))
            
        # Add current message
        content = []
        if user_message:
            content.append({"type": "text", "text": user_message})
        elif image_bytes:
            content.append({"type": "text", "text": "Can you describe this image for me?"})
            
        if image_bytes:
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
            
        messages.append(("human", content))
        
        try:
            response: AssistantAction = await self.structured_llm.ainvoke(messages)
            return response
        except Exception as e:
            logger.error(f"Error calling Gemini Structured API: {str(e)}")
            return AssistantAction(reply="I'm sorry, I'm having trouble processing your request right now. Please try again later.", memory_to_save=None, reminders=None)

# Singleton instance
gemini_client = GeminiClient()
