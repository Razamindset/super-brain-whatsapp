from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.whatsapp.sender import whatsapp_sender
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Prefix used on snooze/done button IDs so the conversation manager can detect them
REMINDER_DONE_PREFIX   = "reminder_done::"
REMINDER_SNOOZE_10_PREFIX = "reminder_snooze_10::"
REMINDER_SNOOZE_60_PREFIX = "reminder_snooze_60::"


async def _fire_reminder(to_number: str, reminder_text: str):
    """
    Fires a rich interactive reminder message with action buttons.
    Called by APScheduler when the job triggers.
    """
    body = (
        "🔔 *Reminder*\n"
        "━━━━━━━━━━━━━━━━\n"
        f"{reminder_text}\n"
        "━━━━━━━━━━━━━━━━"
    )
    buttons = [
        {"id": f"{REMINDER_DONE_PREFIX}{reminder_text[:50]}", "title": "✅ Done"},
        {"id": f"{REMINDER_SNOOZE_10_PREFIX}{reminder_text[:50]}", "title": "⏰ +10 min"},
        {"id": f"{REMINDER_SNOOZE_60_PREFIX}{reminder_text[:50]}", "title": "⏰ +1 hour"},
    ]
    await whatsapp_sender.send_interactive_buttons(to_number, body, buttons)
    logger.info(f"Fired reminder to {to_number}: {reminder_text[:60]}")


class SchedulerEngine:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.start()
        logger.info("APScheduler started.")

    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("APScheduler shutdown.")

    def schedule_reminder(self, to_number: str, reminder_text: str, run_date: datetime):
        """
        Schedules a rich interactive reminder at run_date.
        """
        try:
            self.scheduler.add_job(
                _fire_reminder,
                'date',
                run_date=run_date,
                kwargs={"to_number": to_number, "reminder_text": reminder_text}
            )
            logger.info(f"Scheduled reminder to {to_number} at {run_date}: {reminder_text[:60]}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {e}")
            return False

    def schedule_message(self, to_number: str, message: str, run_date: datetime):
        """
        Legacy plain-text schedule — kept for backward compatibility.
        Prefer schedule_reminder for user-facing reminders.
        """
        return self.schedule_reminder(to_number, message, run_date)


scheduler_engine = SchedulerEngine()
