"""
Claude-powered Telegram bot.

Setup:
  1. Copy .env.example to .env and fill in your keys.
  2. pip install -r requirements.txt
  3. python bot.py

Commands:
  /start  — welcome message
  /reset  — clear conversation history
  /help   — show help
"""

import logging
import os
from collections import defaultdict

import anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MODEL = "claude-opus-4-6"
MAX_HISTORY = 40  # max messages kept per user (user+assistant pairs)

anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Per-user conversation history: {user_id: [{"role": ..., "content": ...}, ...]}
histories: dict[int, list[dict]] = defaultdict(list)

SYSTEM_PROMPT = (
    "You are a helpful, thoughtful assistant running inside Telegram. "
    "Keep responses concise but complete. Use plain text — avoid markdown "
    "formatting since Telegram may not render it in all contexts."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm powered by Claude. Send me any message and I'll respond.\n\n"
        "Commands:\n"
        "  /reset — clear our conversation history\n"
        "  /help  — show this message"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    histories[user_id].clear()
    await update.message.reply_text("Conversation cleared. Fresh start!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if not user_text:
        return

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    history = histories[user_id]
    history.append({"role": "user", "content": user_text})

    # Trim history to stay within limits (keep pairs)
    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    try:
        reply = _call_claude(history)
        history.append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except anthropic.APIError as exc:
        logger.error("Anthropic API error: %s", exc)
        # Remove the unanswered user turn so history stays consistent
        history.pop()
        await update.message.reply_text(
            "Sorry, I ran into an error talking to Claude. Please try again."
        )


def _call_claude(messages: list[dict]) -> str:
    """Send messages to Claude and return the full response text."""
    with anthropic_client.messages.stream(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        messages=messages,
    ) as stream:
        return stream.get_final_message().content[0].text


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started. Polling for updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
