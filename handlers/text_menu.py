from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_text = (
        "📋 Главное меню:\n\n"
        "🖥️ /status — Статус сервера\n"
        "📊 /topvoters — Топ голосующих\n"
        "🧠 /topplayers — Топ игроков\n"
        "👥 /online — Онлайн-игроки\n"
        "🔄 /menu — Обновить меню"
    )
    await update.message.reply_text(menu_text)

menu_handlers = [
    CommandHandler("menu", main_menu),
]
