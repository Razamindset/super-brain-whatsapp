from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.whatsapp.sender import whatsapp_sender
from app.database.supabase_impl import db
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Prefix used on snooze/done button IDs so the conversation manager can detect them
REMINDER_DONE_PREFIX   = "reminder_done::"
REMINDER_SNOOZE_10_PREFIX = "reminder_snooze_10::"
REMINDER_SNOOZE_60_PREFIX = "reminder_snooze_60::"


async def _fire_reminder(to_number: str, reminder_text: str, reminder_id: str):
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
        {"id": f"{REMINDER_DONE_PREFIX}{reminder_id}", "title": "✅ Done"},
        {"id": f"{REMINDER_SNOOZE_10_PREFIX}{reminder_id}", "title": "⏰ +10 min"},
        {"id": f"{REMINDER_SNOOZE_60_PREFIX}{reminder_id}", "title": "⏰ +1 hour"},
    ]
    await whatsapp_sender.send_interactive_buttons(to_number, body, buttons)
    
    # Mark as fired in DB
    await db.mark_reminder_fired(reminder_id)
    logger.info(f"Fired reminder {reminder_id} to {to_number}")


class SchedulerEngine:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.start()
        logger.info("APScheduler started.")

    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("APScheduler shutdown.")

    async def load_reminders(self):
        """Reload all pending reminders from DB into APScheduler (startup recovery)."""
        reminders = await db.get_all_pending_reminders()
        count = 0
        for r in reminders:
            run_date = datetime.fromisoformat(r["run_at"])
            # If run_date is in the past, fire it now
            if run_date < datetime.now(run_date.tzinfo):
                run_date = datetime.now(run_date.tzinfo) + timedelta(seconds=2)
            
            try:
                self.scheduler.add_job(
                    _fire_reminder,
                    'date',
                    run_date=run_date,
                    id=r["id"],
                    kwargs={
                        "to_number": r["user_id"],
                        "reminder_text": r["text"],
                        "reminder_id": r["id"]
                    },
                    replace_existing=True
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to reload reminder {r['id']}: {e}")
        
        if count > 0:
            logger.info(f"Recovered {count} pending reminders from database.")

    def schedule_reminder(self, to_number: str, reminder_text: str, run_date: datetime, reminder_id: str):
        """
        Schedules a rich interactive reminder at run_date.
        """
        try:
            self.scheduler.add_job(
                _fire_reminder,
                'date',
                run_date=run_date,
                id=reminder_id,
                kwargs={
                    "to_number": to_number, 
                    "reminder_text": reminder_text,
                    "reminder_id": reminder_id
                },
                replace_existing=True
            )
            logger.info(f"Scheduled reminder {reminder_id} to {to_number} at {run_date}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {e}")
            return False

    async def cancel_reminder(self, reminder_id: str) -> bool:
        """Removes a job from the scheduler and updates DB status."""
        success = await db.cancel_reminder(reminder_id)
        try:
            self.scheduler.remove_job(reminder_id)
            logger.info(f"Removed job {reminder_id} from scheduler.")
        except Exception:
            # Might already be fired or gone
            pass
        return success

    def schedule_message(self, to_number: str, message: str, run_date: datetime):
        """
        Legacy plain-text schedule — kept for backward compatibility.
        Prefer schedule_reminder for user-facing reminders.
        """
        return self.schedule_reminder(to_number, message, run_date)


scheduler_engine = SchedulerEngine()
