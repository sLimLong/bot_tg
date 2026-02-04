import logging
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from config import ( TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_THREAD_ID, DISCORD_WEBHOOK_URL, DISCORD_ROLE_IDS )


# 📤 Отправка текста в Discord через webhook
async def post_to_discord(text: str):
    content = text.strip()
    if not content:
        logging.warning("⚠️ Пустое сообщение — не отправляем")
        return

    mentions = " ".join(f"<@&{rid}>" for rid in DISCORD_ROLE_IDS)
    payload = {"content": f"{mentions}\n\n{content}" if mentions else content}

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(DISCORD_WEBHOOK_URL, json=payload) as resp:
                logging.info(f"📡 Discord ответ: {resp.status}")
                if resp.status != 204:
                    logging.warning("📝 %s", await resp.text())
    except Exception as e:
        logging.error(f"❌ Ошибка при отправке в Discord: {e}")

# 📬 Хендлер пересылки текста из нужного чата и топика
async def forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return  # игнорируем медиа, captions без текста и т.п.

    chat_id   = message.chat.id
    thread_id = message.message_thread_id

    logging.info("📥 Получено сообщение: %r", message.text)
    logging.info("📌 chat.id=%s, thread_id=%s, is_topic=%s",
                 chat_id, thread_id, message.is_topic_message)

    if chat_id == TELEGRAM_CHAT_ID and thread_id == TELEGRAM_THREAD_ID:
        logging.info("📡 Условие выполнено — отправляем в Discord")
        await post_to_discord(message.text)
    else:
        logging.info("⛔ Не тот чат или топик — игнор")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Ловим _только_ текстовые сообщения из заданного чата
    text_filter = filters.Chat(TELEGRAM_CHAT_ID) & filters.TEXT
    app.add_handler(MessageHandler(text_filter, forward_handler))

    logging.info("🚀 Бот запущен, начинает опрос Telegram…")
    app.run_polling()

if __name__ == "__main__":
    main()
