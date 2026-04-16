import asyncio
import uuid
import phonenumbers
from phonenumbers.timezone import time_zones_for_number
import pytz
from datetime import datetime, timedelta
from app.database.supabase_impl import db
from app.llm.gemini_client import gemini_client
from app.rag.indexer import indexer
from app.rag.engine import engine
from app.whatsapp.sender import whatsapp_sender
from app.scheduler.engine import (
    scheduler_engine,
    REMINDER_DONE_PREFIX,
    REMINDER_SNOOZE_10_PREFIX,
    REMINDER_SNOOZE_60_PREFIX,
)
import logging

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self):
        self.system_instruction = (
            "You are a helpful personal assistant on WhatsApp. "
            "You have access to the user's previous conversations and relevant personal notes (memories). "
            "Use the provided context to answer accurately. If you don't know something, just say you don't know. "
            "MEMORY MANAGEMENT: When relevant memories are provided, they include a unique ID in the format [mem_id:UUID]. "
            "If the user says something that CONTRADICTS or UPDATES an existing memory (e.g., they previously said 'use emojis' "
            "but now say 'stop using emojis'), you MUST: (1) save the new memory via memory_to_save, and (2) delete the "
            "conflicting old memory by putting its UUID in memory_ids_to_delete."
        )

    def get_user_timezone(self, phone_number_str: str) -> str:
        if not phone_number_str.startswith('+'):
            phone_number_str = '+' + phone_number_str
        try:
            parsed_num = phonenumbers.parse(phone_number_str)
            tz_list = time_zones_for_number(parsed_num)
            if tz_list and tz_list[0] != 'Etc/Unknown':
                return tz_list[0]
        except Exception:
            pass
        return "UTC"

    async def handle_message(self, from_number: str, message_text: str, media_id: str = None, button_id: str = None):
        """
        Main orchestration logic for handling an incoming WhatsApp message.
        """
        user_id = from_number
        image_bytes = None

        # ── REMINDER ACTION INTERCEPT ────────────────────────────────────────
        # Must run BEFORE anything else so we don't log these as conversations.
        if button_id:
            if button_id.startswith(REMINDER_DONE_PREFIX):
                await whatsapp_sender.send_message(
                    user_id,
                    "✅ *Great job!* Reminder marked as done. 🎉"
                )
                return

            elif button_id.startswith(REMINDER_SNOOZE_10_PREFIX):
                reminder_text = button_id[len(REMINDER_SNOOZE_10_PREFIX):]
                snooze_until = datetime.now(pytz.utc) + timedelta(minutes=10)
                scheduler_engine.schedule_reminder(user_id, reminder_text, snooze_until)
                user_tz_str = self.get_user_timezone(user_id)
                local_snooze = snooze_until.astimezone(pytz.timezone(user_tz_str))
                await whatsapp_sender.send_message(
                    user_id,
                    f"⏰ Got it! I'll remind you again at *{local_snooze.strftime('%H:%M')}*."
                )
                return

            elif button_id.startswith(REMINDER_SNOOZE_60_PREFIX):
                reminder_text = button_id[len(REMINDER_SNOOZE_60_PREFIX):]
                snooze_until = datetime.now(pytz.utc) + timedelta(hours=1)
                scheduler_engine.schedule_reminder(user_id, reminder_text, snooze_until)
                user_tz_str = self.get_user_timezone(user_id)
                local_snooze = snooze_until.astimezone(pytz.timezone(user_tz_str))
                await whatsapp_sender.send_message(
                    user_id,
                    f"⏰ No rush! I'll remind you again at *{local_snooze.strftime('%H:%M')}*."
                )
                return
        # ── END REMINDER ACTION INTERCEPT ────────────────────────────────────

        user_tz_str = self.get_user_timezone(user_id)
        user_tz = pytz.timezone(user_tz_str)
        local_time = datetime.now(user_tz)
        
        if media_id:
            image_bytes = await whatsapp_sender.download_media(media_id)

        # 1. Ensure user exists and get onboarding state
        user_record = await db.ensure_user(user_id)
        
        # --- ONBOARDING INTERCEPT ---
        if user_record and not user_record.get("is_onboarded"):
            step = user_record.get("onboarding_step", "start")
            
            if step == "start":
                body = "👋 Welcome to *Super Brain*! I am your personal AI assistant.\n\nTo get started, what should I call you?"
                await whatsapp_sender.send_message(user_id, body)
                await db.update_user_onboarding(user_id, {"onboarding_step": "ask_name"})
                return
                
            elif step == "ask_name":
                name = message_text.strip()
                await db.update_user_onboarding(user_id, {"name": name, "onboarding_step": "ask_preferences"})
                sections = [{
                    "title": "Response Tone",
                    "rows": [
                        {"id": "formal", "title": "Formal & Direct", "description": "Crisp and professional"},
                        {"id": "casual", "title": "Casual & Friendly", "description": "Relaxed with emojis"},
                        {"id": "sarcastic", "title": "Witty Humor", "description": "A bit of sarcastic banter"}
                    ]
                }]
                await whatsapp_sender.send_interactive_list(
                    user_id, 
                    f"Nice to meet you, {name}! How would you like me to respond to you generally? (You can click the button below to choose).",
                    "Select Tone",
                    sections
                )
                return
                
            elif step == "ask_preferences":
                tone = message_text.strip()
                prefs = user_record.get("preferences", {})
                prefs["tone"] = tone
                await db.update_user_onboarding(user_id, {
                    "preferences": prefs,
                    "is_onboarded": True,
                    "onboarding_step": "complete"
                })
                await whatsapp_sender.send_interactive_buttons(
                    user_id, 
                    f"Awesome! I've set your tone to *{tone}*. You're fully set up! Are you ready?", 
                    [{"id": "ready_yes", "title": "Let's Go!"}]
                )
                return
        # --- END ONBOARDING ---

        # 2. Regular message processing
        if message_text.lower().startswith("remember this:"):
            content_to_remember = message_text[len("remember this:"):].strip()
            doc_id = str(uuid.uuid4())

            # Find semantically similar existing memories so we can detect conflicts
            similar_mems = await engine.query(content_to_remember, user_id, k=5)
            similar_context = "\n".join(
                [f"- [mem_id:{m['id']}] {m['document_text']}" for m in similar_mems]
            )

            # Ask the LLM to handle de-duplication / conflict resolution
            dedup_instruction = (
                self.system_instruction +
                "\n\nThe user has explicitly asked you to remember something new. "
                "Your job is to store it and clean up any conflicting old memories. "
                "Set memory_to_save to the canonical fact. "
                "Set memory_ids_to_delete to any [mem_id:UUID] entries below that this new memory CONTRADICTS or REPLACES. "
                "Reply with a short confirmation (e.g. \"Got it! I've updated that.\")."
            )
            if similar_context:
                dedup_instruction += f"\n\nExisting relevant memories:\n{similar_context}"

            action = await gemini_client.get_response(dedup_instruction, [], content_to_remember)

            # Save new memory
            if action.memory_to_save:
                vector = await indexer.get_embedding(action.memory_to_save)
                if vector:
                    await db.save_document(user_id, action.memory_to_save, doc_id, vector)

            # Delete stale/conflicting memories
            if action.memory_ids_to_delete:
                for stale_id in action.memory_ids_to_delete:
                    logger.info(f"Deleting stale memory {stale_id} for {user_id}")
                    await db.delete_memory(stale_id)

            await whatsapp_sender.send_message(user_id, action.reply or "✅ Got it! I've remembered that for you.")
            return

        # 2a. Retrieve context from RAG (returns dicts with 'id' and 'document_text')
        rag_results = await engine.query(message_text, user_id)
        # Build context string: include IDs so LLM can reference them for conflict resolution
        rag_context = "\n".join(
            [f"- [mem_id:{m['id']}] {m['document_text']}" for m in rag_results]
        )
        
        # 2b. Retrieve conversation history
        history = await db.get_conversation_history(user_id, limit=5)
        
        # Extract personalization
        user_name = user_record.get("name", "User") if user_record else "User"
        user_prefs = user_record.get("preferences", {}) if user_record else {}
        
        # 2c. Build Augmented Prompt
        full_system_instruction = self.system_instruction + f"\n\nCURRENT CONTEXT: The user's name is {user_name}. Their preferences are: {user_prefs}. The user's timezone is roughly {user_tz_str}. The current exact local time and date for the user is {local_time.isoformat()}."
        if rag_context:
            full_system_instruction += f"\n\nRelevant user notes/information:\n{rag_context}"
            
        # 2d. Call Gemini for Structured Processing
        action = await gemini_client.get_response(full_system_instruction, history, message_text, image_bytes)

        # 2e. Send WhatsApp reply IMMEDIATELY — user gets response right away
        if action.interactive_widget:
            w_type = action.interactive_widget.get("type")
            if w_type == "button":
                opts = action.interactive_widget.get("options", [])
                buttons = [{"id": f"btn_{i}", "title": opt} for i, opt in enumerate(opts[:3])]
                await whatsapp_sender.send_interactive_buttons(user_id, action.reply, buttons)
            elif w_type == "list":
                btn_label = action.interactive_widget.get("button_label", "Select")
                sects = action.interactive_widget.get("sections", [])
                await whatsapp_sender.send_interactive_list(user_id, action.reply, btn_label, sects)
            else:
                await whatsapp_sender.send_message(user_id, action.reply)
        else:
            await whatsapp_sender.send_message(user_id, action.reply)

        # 2f. Schedule any reminders (in-process, near-instant — no need to parallelize)
        if action.reminders:
            for rm in action.reminders:
                try:
                    run_datetime = datetime.fromisoformat(rm.time.replace("Z", "+00:00"))
                    scheduler_engine.schedule_reminder(user_id, rm.text, run_datetime)
                except Exception as e:
                    logger.error(f"Failed to parse reminder time {rm.time}: {e}")

        # 2g. Fire all DB writes concurrently — don't make the user wait for housekeeping
        async def _save_conversation():
            await db.save_conversation(
                user_id, message_text or "[Image Uploaded]", action.reply, "gemini-pro-structured"
            )

        async def _save_memory():
            if action.memory_to_save:
                logger.info(f"Auto-saving memory for {user_id}: {action.memory_to_save}")
                doc_id = str(uuid.uuid4())
                vector = await indexer.get_embedding(action.memory_to_save)
                if vector:
                    await db.save_document(user_id, action.memory_to_save, doc_id, vector)

        async def _delete_stale_memories():
            if action.memory_ids_to_delete:
                for stale_id in action.memory_ids_to_delete:
                    logger.info(f"Deleting stale memory {stale_id} for {user_id}")
                    await db.delete_memory(stale_id)

        await asyncio.gather(
            _save_conversation(),
            _save_memory(),
            _delete_stale_memories(),
            return_exceptions=True  # DB errors don't crash the handler
        )

manager = ConversationManager()
