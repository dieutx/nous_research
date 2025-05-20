# bot_telegram.py

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
import requests
import logging
from logging.handlers import RotatingFileHandler

# Logging configuration with file rotation
logging.basicConfig(
    handlers=[RotatingFileHandler("bot_logs.txt", maxBytes=10*1024*1024, backupCount=5)],
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)

# Prompt user for sensitive keys at startup
NOUS_API_KEY = input("Enter your Nous Research API key: ").strip()
BOT_TOKEN      = input("Enter your Telegram bot token: ").strip()

# Model to use
MODEL = "Hermes-3-Llama-3.1-405B"

def call_nous(prompt):
    url = "https://inference-api.nousresearch.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NOUS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        error_msg = f"API error: Status code {response.status_code}"
        logging.error(f"[ERROR] {error_msg}\nRaw response: {response.text}")
        return "An error occurred while contacting the API. Please try again later."

    try:
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"[ERROR] API error: {e}\nRaw response: {response.text}")
        return "An error occurred. Please try again later."

async def start(update: Update, context: ContextTypes):
    await update.message.reply_text("Hello! I’m a bot that answers your questions. Just send me a message!")

async def handle_message(update: Update, context: ContextTypes):
    user = update.message.from_user
    user_input = update.message.text
    ai_response = call_nous(user_input)

    print(f"[USER] {user.username} (ID: {user.id})")
    print(f"[INPUT] {user_input}")
    print(f"[RESPONSE] {ai_response}\n")

    logging.info(f"[USER] {user.username} (ID: {user.id})")
    logging.info(f"[INPUT] {user_input}")
    logging.info(f"[RESPONSE] {ai_response}\n")

    if len(ai_response) > 4096:
        parts = [ai_response[i:i+4096] for i in range(0, len(ai_response), 4096)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(ai_response)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text() & ~filters.Command(), handle_message))
    print("🤖 Bot is running...")
    app.run_polling()
