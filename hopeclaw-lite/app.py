import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    TELEGRAM_BOT_TOKEN, BOT_NAME,
    WEBHOOK_URL, WEBHOOK_PORT, WEBHOOK_PATH, WEBHOOK_CERT, WEBHOOK_KEY,
)
from memory import init_db
from agent import call_llm, parse_tool
from tools import run_tool
from scheduler import process_due_reminders

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'{BOT_NAME} online. Ask me anything.')

async def cmd_memory(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from memory import list_memories
    rows = list_memories()
    text = '\n'.join(f'- {k}: {v}' for k, v, _ in rows) if rows else 'No memories yet.'
    await update.message.reply_text(text)

async def cmd_reminders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from memory import list_reminders
    rows = list_reminders()
    text = '\n'.join(f'- {r[1]} @ {r[2]}' for r in rows) if rows else 'No reminders.'
    await update.message.reply_text(text)

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    await ctx.bot.send_chat_action(update.effective_chat.id, 'typing')
    try:
        llm_output = call_llm(user_text)
    except Exception as e:
        await update.message.reply_text(f'LLM error: {e}')
        return

    tool_call = parse_tool(llm_output)
    if tool_call:
        tool_name, args = tool_call
        if tool_name == 'add_reminder':
            args = args + [str(update.effective_chat.id)]
        result = run_tool(tool_name, *args)
        await update.message.reply_text(result)
        return

    await update.message.reply_text(llm_output)

def main():
    init_db()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('memory', cmd_memory))
    app.add_handler(CommandHandler('reminders', cmd_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: asyncio.ensure_future(process_due_reminders(app.bot)),
        'interval', seconds=30
    )
    scheduler.start()

    if WEBHOOK_URL:
        import os
        from telegram.ext import Updater
        cert = open(WEBHOOK_CERT, 'rb') if os.path.exists(WEBHOOK_CERT) else None
        app.run_webhook(
            listen='0.0.0.0',
            port=WEBHOOK_PORT,
            url_path=WEBHOOK_PATH,
            webhook_url=f'{WEBHOOK_URL.rstrip("/")}{WEBHOOK_PATH}',
            cert=cert,
            key=WEBHOOK_KEY if os.path.exists(WEBHOOK_KEY) else None,
            drop_pending_updates=True,
        )
        if cert:
            cert.close()
    else:
        app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
