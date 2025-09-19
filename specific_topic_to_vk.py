import logging
import aiohttp
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

# 🔑 Настройки
VK_TOKEN = "vk1.a.fWx8Je9RjMwNhr2Xx-1q8EAcHrGLGYNcNE9RY-KZ56rbDwHof-CybEruoUmpLM-yRNiZ_Rl3RE5gw6wm9bsE9eWF3EgVzzeZI9eDyldxYwQrocv6yNmavgm6tWM9SiroYR_po_GX1o1al3jsytIdn0tXsYEYbgblkNocEoFfZjQYJtfEE1D606pwBL0LiXgx4iQaJqbnp3-Lm35lcIhkoA"
VK_GROUP_ID = 148250057
TELEGRAM_GROUP_ID = -1002418675036
TARGET_THREAD_ID = 31  # ID нужного топика

# 📤 Асинхронная отправка в VK
async def post_to_vk(text: str, message_id: int):
    if not text.strip():
        logging.warning("⚠️ Пустое сообщение — не публикуем")
        return

    post_link = f"https://t.me/c/{str(TELEGRAM_GROUP_ID)[4:]}/{message_id}"
    full_text = f"{text}\n\n🔗 Оригинал в Telegram: {post_link}"

    params = {
        "access_token": VK_TOKEN,
        "owner_id": -VK_GROUP_ID,
        "message": full_text,
        "v": "5.131"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.vk.com/method/wall.post", params=params) as response:
                status = response.status
                raw = await response.text()
                logging.debug(f"📡 VK HTTP status: {status}")
                logging.debug(f"📡 VK raw response: {raw}")

                result = await response.json()
                if "error" in result:
                    logging.error(f"❌ VK Error: {result['error']['error_msg']}")
                else:
                    logging.info("📤 Пост опубликован в VK")
    except Exception as e:
        logging.error(f"❌ Ошибка при отправке в VK: {e}")

# 📬 Асинхронный хендлер Telegram
async def specific_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    logging.info(f"📥 Получено сообщение: {message.text}")
    logging.info(f"📌 chat.id={message.chat.id}, thread_id={message.message_thread_id}, is_topic={message.is_topic_message}")

    if (
        message.chat.id == TELEGRAM_GROUP_ID and
        message.is_topic_message and
        message.message_thread_id == TARGET_THREAD_ID
    ):
        logging.info("📡 Условие выполнено — отправляем в VK")
        text = message.text or ""
        await post_to_vk(text, message.message_id)
    else:
        logging.info("⛔ Сообщение не соответствует условиям — игнор")

# 📦 Экспорт хендлера для main.py
topic_handler = MessageHandler(filters.ChatType.SUPERGROUP & filters.TEXT, specific_topic_handler)
