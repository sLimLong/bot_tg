# players.py

import requests, logging, time, re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from config import SERVERS

PLAYERS_COOLDOWN = 120

def escape_markdown(text: str) -> str:
    return re.sub(r'([_*[\]()~`>#+\-=|{}.!])', r'\\\1', text)

# 📍 Команда /players — показывает кнопки с онлайн
async def players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for i, server in enumerate(SERVERS):
        try:
            response = requests.get(
                f"{server['url']}/api/getplayersonline",
                auth=server['auth'],
                timeout=5
            )
            players = response.json()
            count = len(players) if isinstance(players, list) else 0
        except Exception as e:
            logging.warning(f"[players] {server['name']} — ошибка: {e}")
            count = 0

        button_text = f"{server['name']} ({count})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"players_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите сервер:", reply_markup=reply_markup)

# 📡 Обработка нажатия кнопки
async def players_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    now = time.time()
    last_used = context.user_data.get("players_last_used", 0)
    remaining = int(PLAYERS_COOLDOWN - (now - last_used))

    if remaining > 0:
        await query.edit_message_text(f"⏳ Подождите {remaining} сек. перед следующим запросом.")
        return

    context.user_data["players_last_used"] = now

    index = int(query.data.split("_")[1])
    server = SERVERS[index]
    messages = []

    try:
        response = requests.get(
            f"{server['url']}/api/getplayersonline",
            auth=server['auth'],
            timeout=5
        )
        players = response.json()

        if not isinstance(players, list) or not players:
            messages.append(f"🖥️ {escape_markdown(server['name'])} — никто не онлайн")
        else:
            players.sort(key=lambda p: p.get("name", "").lower())
            lines = [f"• {escape_markdown(p.get('name', '?'))}" for p in players]
            messages.append(
                f"🖥️ {escape_markdown(server['name'])} — онлайн ({len(players)}):\n" + "\n".join(lines)
            )

    except Exception as e:
        logging.warning(f"[players] {server['name']} — ошибка: {e}")
        messages.append(f"❌ {escape_markdown(server['name'])} — ошибка: {escape_markdown(str(e))}")

    await query.edit_message_text("\n\n".join(messages), parse_mode="Markdown")

# 📦 Экспорт хендлеров
players_handler = CommandHandler("players", players)
players_callback_handler = CallbackQueryHandler(players_callback, pattern=r"^players_\d+$")
