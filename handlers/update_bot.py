import os
import subprocess
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import ALLOWED_ADMINS

BOT_DIR = "/root/bot_tg"
SERVICE_NAME = "bot_tg.service"

async def update_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_ADMINS:
        await update.message.reply_text("⛔ Недостаточно прав.")
        return

    await update.message.reply_text("🔄 Обновление началось...")

    try:
        os.chdir(BOT_DIR)

        subprocess.check_call(["git", "pull"])
        subprocess.check_call(["pip3", "install", "-r", "requirements.txt"])
        subprocess.run(["systemctl", "restart", SERVICE_NAME])

        await update.message.reply_text("✅ Обновление и перезапуск прошли успешно.")

    except subprocess.CalledProcessError:
        await update.message.reply_text("❌ Обновление не удалось. Проверь журнал ошибок.")

    except Exception as e:
        await update.message.reply_text(f"❌ Непредвиденная ошибка: {str(e)}")

def get_handler():
    return CommandHandler("update_bot", update_bot_handler)
