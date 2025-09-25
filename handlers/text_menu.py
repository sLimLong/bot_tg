from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def player_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎮 <b>Игровое меню</b>\n\n"
        "🖥️ <b>Информация о сервере</b>\n"
        "/status — статус сервера\n"
        "/players — кто сейчас онлайн\n"
        "/whoami — кто я в системе\n"
        "/whois [имя] — информация об игроке\n\n"
        "📊 <b>Статистика</b>\n"
        "/topplayers — топ игроков по онлайну\n"
        "/topvoters — топ голосующих\n\n"
        "📋 <b>Прочее</b>\n"
        "/menu — главное меню\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")

# 📦 Экспорт хендлеров
menu_handlers = [CommandHandler("menu", player_menu_command)]
