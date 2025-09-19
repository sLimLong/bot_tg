from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import ALLOWED_ADMINS
import importlib

async def reload_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_ADMINS:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return

    try:
        importlib.reload(__import__("config"))
        await update.message.reply_text("✅ Конфиг успешно перезагружен.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при перезагрузке: {e}")

reload_config_handler = CommandHandler("reload_config", reload_config_command)
