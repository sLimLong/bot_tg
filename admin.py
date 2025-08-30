# admin.py

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ContextTypes
)
from config import SERVERS, ALLOWED_ADMINS

# 🛠️ /admin — запуск панели
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_ADMINS:
        await update.message.reply_text("⛔ Нет доступа.")
        return
    keyboard = [[InlineKeyboardButton(s["name"], callback_data=f"admin_{i}")] for i, s in enumerate(SERVERS)]
    await update.message.reply_text("Выберите сервер:", reply_markup=InlineKeyboardMarkup(keyboard))

# ⚙️ Выбор сервера → действия
async def handle_admin_server_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace("admin_", ""))
    server = SERVERS[index]
    context.user_data["selected_server"] = server["name"]
    context.user_data["selected_index"] = index

    keyboard = [
        [InlineKeyboardButton("🔁 Перезапуск", callback_data="action_restart")],
        [InlineKeyboardButton("⛔ Отключение", callback_data="action_shutdown")],
        [InlineKeyboardButton("📍 Кик", callback_data="action_kick")],
        [InlineKeyboardButton("📍 Бан", callback_data="action_ban")],
        [InlineKeyboardButton("📍 Бан на всех серверах", callback_data="action_banall")],
        [InlineKeyboardButton("📣 Broadcast", callback_data="action_broadcast")],
        [InlineKeyboardButton("👥 Онлайн игроки", callback_data="action_players")],
        [InlineKeyboardButton("🔍 Игрок по EntityID", callback_data="action_apl")],
        [InlineKeyboardButton("📘 Команды бота", callback_data="action_commands")]
    ]
    await query.edit_message_text(f"Сервер: {server['name']}\nВыберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

# 🚨 Обработка действия
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.replace("action_", "")
    server_name = context.user_data.get("selected_server")
    index = context.user_data.get("selected_index", 0)
    server = SERVERS[index]

    if action == "restart":
        await query.edit_message_text(f"🔁 {server_name} — перезапуск инициирован (заглушка)")
    elif action == "shutdown":
        await query.edit_message_text(f"⛔ {server_name} — отключение инициировано (заглушка)")
    elif action == "broadcast":
        await query.edit_message_text("📣 Введите сообщение для канала:")
        context.user_data["broadcast_mode"] = True
    elif action == "players":
        try:
            response = requests.get(f"{server['url']}/api/getplayersonline", auth=server['auth'], timeout=5)
            players = response.json()
            if not isinstance(players, list) or not players:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"👥 {server['name']} — никто не онлайн")
            else:
                lines = [
                    f"• {p.get('name','?')}\n `{p.get('steamid','—')}`\n ID: `{p.get('entityid','—')}`\n ----"
                    for p in players
                ]
                text = f"👥 {server['name']} — онлайн ({len(players)}):\n" + "\n".join(lines)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode="Markdown")
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Ошибка: {e}")
    elif action == "apl":
        await query.message.reply_text(
            "🔍 Чтобы получить информацию об игроке, используйте команду:\n`/apl <EntityID>`",
            parse_mode="Markdown"
        )
    elif action == "kick":
        await query.message.reply_text(
            "📍 Команда `/kick` запускает диалог:\n\n"
            "1. Выбор сервера\n"
            "2. Ввод EntityID\n\n"
            "Просто напишите `/kick` в чат.",
            parse_mode="Markdown"
        )
    elif action == "ban":
        await query.message.reply_text(
            "📍 Команда `/ban` запускает диалог:\n\n"
            "1. Выбор сервера\n"
            "2. Ввод SteamID64\n"
            "3. Причина\n"
            "4. Срок\n\n"
            "Просто напишите `/ban` в чат.",
            parse_mode="Markdown"
        )
    elif action == "banall":
        await query.message.reply_text(
            "📍 Команда `/banall` запускает диалог:\n\n"
            "1. Ввод SteamID64\n"
            "2. Причина\n"
            "3. Срок\n\n"
            "Просто напишите `/banall` в чат.",
            parse_mode="Markdown"
        )
    elif action == "commands":
        await query.message.reply_text(
            "📘 Команды бота:\n\n"
            "• /kick — кик игрока (по EntityID)\n"
            "• /ban — бан игрока (по SteamID64)\n"
            "• /banall — бан игрока на всех серверах\n"
            "• /apl <EntityID> — информация об игроке\n"
            "• /admin — открыть админ-панель\n"
            "• /cancel — отменить текущую операцию",
            parse_mode="Markdown"
        )

# 📦 Экспорт хендлеров
admin_handlers = [
    CommandHandler("admin", admin_panel),
    CallbackQueryHandler(handle_admin_server_choice, pattern=r"^admin_"),
    CallbackQueryHandler(handle_admin_action, pattern=r"^action_")
]
