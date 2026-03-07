#!/usr/bin/env python3
"""Sophia — Telegram bot powered by Kimi (Moonshot AI)"""

import logging
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8711246322:AAFYrlmgPBES7mlS6Hbj5hIM5O5cjFOPgdI"
KIMI_API_KEY   = "sk-kimi-KhXNhfGAOEJt6HZDylvOrT59JpQPWesrWWUNhNtPBcTgc5Ovzh4pj9nSgUHHoDw4"
KIMI_MODEL     = "moonshot-v1-8k"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

kimi = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1")

SYSTEM_PROMPT = (
    "You are Sophia, a smart and friendly AI assistant. "
    "Be concise, helpful, and natural in conversation."
)

# Per-user conversation history
histories: dict[int, list[dict]] = {}

def get_history(user_id: int) -> list[dict]:
    if user_id not in histories:
        histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return histories[user_id]

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm Sophia, your AI assistant powered by Kimi. Ask me anything!"
    )

async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    histories.pop(update.effective_user.id, None)
    await update.message.reply_text("Conversation cleared. Fresh start!")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text    = update.message.text

    history = get_history(user_id)
    history.append({"role": "user", "content": text})

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    try:
        resp = kimi.chat.completions.create(model=KIMI_MODEL, messages=history)
        reply = resp.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        # Keep history from growing too large (last 20 turns + system)
        if len(history) > 41:
            histories[user_id] = [history[0]] + history[-40:]
    except Exception as e:
        log.error("Kimi error: %s", e)
        reply = "Sorry, I hit an error. Please try again."

    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Sophia bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
