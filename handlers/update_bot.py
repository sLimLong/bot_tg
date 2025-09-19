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

        git_result = subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT).decode()
        pip_result = subprocess.check_output(["pip3", "install", "-r", "requirements.txt"], stderr=subprocess.STDOUT).decode()

        await update.message.reply_text(
            "✅ Обновление завершено.\n\n📦 Git:\n" + git_result +
            "\n🐍 Pip:\n" + pip_result +
            "\n\n🔁 Перезапускаюсь..."
        )

        subprocess.run(["systemctl", "restart", SERVICE_NAME])

    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ Ошибка:\n{e.output.decode()}")

    except Exception as e:
        await update.message.reply_text(f"❌ Непредвиденная ошибка:\n{str(e)}")

def get_handler():
    return CommandHandler("update_bot", update_bot_handler)
