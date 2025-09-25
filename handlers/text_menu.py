from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

# Импортируем нужные функции из других модулей
from players import online_command
from status import status_menu
from top_voters import top_voters_command
from top_playerstats import topstats_command

# 📋 Главное меню (текстовое)
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

# 📦 Обработчики команд
menu_handlers = [
    CommandHandler("menu", main_menu),
    CommandHandler("status", status_menu),
    CommandHandler("topvoters", top_voters_command),
    CommandHandler("topplayers", topstats_command),
    CommandHandler("online", online_command)
]
