import time, requests, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from config import SERVERS, last_request_time, REQUEST_INTERVAL

# 📋 Команда /menu — выбор сервера
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(server["name"], callback_data=f"menu_{i}")]
        for i, server in enumerate(SERVERS)
    ]
    await update.message.reply_text("📋 Выберите сервер:", reply_markup=InlineKeyboardMarkup(keyboard))

# 🎯 Обработка выбора сервера
async def handle_server_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("menu_"):
        return

    try:
        index = int(query.data.replace("menu_", ""))
        server = SERVERS[index]
    except (ValueError, IndexError):
        await query.edit_message_text("❌ Сервер не найден.")
        return

    now = time.time()
    key = (server["name"], "menu")
    if now - last_request_time.get(key, 0) < REQUEST_INTERVAL:
        await query.edit_message_text(f"⏳ {server['name']} — запрос недавно был")
        return

    try:
        response = requests.get(f"{server['url']}/api/getstats", auth=server['auth'], timeout=5)
        data = response.json()

        g = data.get("gametime", {})
        day = g.get("days", 0)
        hour = g.get("hours", 0)
        minute = g.get("minutes", 0)

        left = 7 - (day % 7)
        bloodmoon = "🌕 Сегодня — Красная ночь!" if left == 0 else f"🩸 До КН осталось {left} дней."

        msg = (
            f"🖥️ {server['name']}\n"
            f"📅 День {day}, {hour:02d}:{minute:02d}\n"
            f"👥 Игроков: {data.get('players', '?')}\n"
            f"😈 Врагов: {data.get('hostiles', '?')}\n"
            f"🐾 Животных: {data.get('animals', '?')}\n"
            f"{bloodmoon}"
        )

        last_request_time[key] = now
        await query.edit_message_text(msg)

    except Exception as e:
        logging.warning(f"[menu] Ошибка: {e}")
        await query.edit_message_text(f"❌ Ошибка: {e}")

# 📦 Экспорт хендлеров
status_handlers = [
    CommandHandler("menu", menu),
    CallbackQueryHandler(handle_server_choice, pattern=r"^menu_")
]

# 🕒 Заглушка для фоновых задач
def schedule_jobs(app):
    pass
