from datetime import datetime, timezone
from telegram import Bot
from memory import get_due_reminders, mark_reminder_sent

async def process_due_reminders(bot: Bot):
    now_iso = datetime.now(timezone.utc).isoformat()
    for reminder_id, text, when_iso, chat_id in get_due_reminders(now_iso):
        await bot.send_message(chat_id=chat_id, text=f'Reminder\n{text}')
        mark_reminder_sent(reminder_id)
