from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# Импортируем нужные функции из других модулей
from players import online_command  # функция, которая показывает онлайн-игроков
from status import status_menu      # функция, которая показывает статус сервера
from top_voters import top_voters_command  # функция, которая показывает топ голосующих
from top_playerstats import topstats_command  # функция, которая показывает топ игроков

# 📋 Главное меню
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖥️ Статус сервера", callback_data="info")],
        [InlineKeyboardButton("📊 Топ голосующих", callback_data="topvoters")],
        [InlineKeyboardButton("🧠 Топ игроков", callback_data="top_pl")],
        [InlineKeyboardButton("👥 Онлайн-игроки", callback_data="players")],
        [InlineKeyboardButton("🔄 Обновить меню", callback_data="refresh_menu")]
    ]
    await update.message.reply_text("📋 Главное меню:", reply_markup=InlineKeyboardMarkup(keyboard))

# 🎯 Обработка кнопок меню
async def handle_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == "refresh_menu":
        await query.edit_message_text("🔄 Обновление меню...")
        await main_menu(update, context)

    elif action == "info":
        await status_menu(update, context)

    elif action == "topvoters":
        await top_voters_command(update, context)

    elif action == "top_pl":
        await topstats_command(update, context)

    elif action == "players":
        await online_command(update, context)

    else:
        await query.edit_message_text("❌ Неизвестное действие.")

# 📦 Экспорт хендлеров
menu_handlers = [
    CommandHandler("menu", main_menu),
    CallbackQueryHandler(handle_menu_action, pattern=r"^(info|topvoters|top_pl|players|refresh_menu)$")
]
