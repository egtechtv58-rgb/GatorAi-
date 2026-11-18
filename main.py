import os
import requests
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

MODEL = "gemini-2.5-flash"

URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent"
)

memory = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    memory[update.effective_user.id] = []

    await update.message.reply_text(
        "👋 Welcome to GatorAI 2.0!\n"
        "I'm your personal AI assistant. Ask me anything!"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    memory[update.effective_user.id] = []
    await update.message.reply_text("Conversation reset! 🔄")


def ask_ai(history):
    response = requests.post(
        URL,
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_KEY
        },
        json={"contents": history},
        timeout=45
    )

    response.raise_for_status()

    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    history = memory.get(user_id, [])

    new_history = history + [{
        "role": "user",
        "parts": [{"text": update.message.text}]
    }]

    try:
        await context.bot.send_chat_action(
            update.effective_chat.id,
            "typing"
        )

        answer = await asyncio.to_thread(
            ask_ai,
            new_history
        )

        new_history.append({
            "role": "model",
            "parts": [{"text": answer}]
        })

        memory[user_id] = new_history[-6:]

        await update.message.reply_text(answer[:4000])

    except Exception as e:
        print("ERROR:", repr(e))

        await update.message.reply_text(
            "Sorry! GatorAI is temporarily unavailable. Try again."
        )


def main():
    if not TELEGRAM_TOKEN or not GEMINI_KEY:
        raise ValueError("Missing environment variables!")

    app = Application.builder().token(
        TELEGRAM_TOKEN
    ).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, reply)
    )

    print("GATORAI 2.0 IS ONLINE!")

    app.run_polling()


if __name__ == "__main__":
    main()
