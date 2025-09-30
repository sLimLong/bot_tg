import requests
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)
from telegram.error import TelegramError
from config import SERVERS, ALLOWED_ADMINS

SELECT_SERVER = 0

def is_admin(user_id: int) -> bool:
    return user_id in ALLOWED_ADMINS

# 🌍 Получение региона и метки VPN/Proxy
def get_ip_info(ip: str) -> str:
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=66846719", timeout=3)
        data = response.json()
        country = data.get("country", "—")
        region = data.get("regionName", "—")
        city = data.get("city", "—")
        isp = data.get("isp", "—")

        flags = []
        if data.get("proxy"): flags.append("VPN/Proxy")
        if data.get("hosting"): flags.append("Hosting")
        if data.get("mobile"): flags.append("Mobile")

        warning = f" ⚠️ {' + '.join(flags)}" if flags else ""
        return f"{country}, {region}, {city} — {isp}{warning}"
    except:
        return "не удалось определить"

# 📊 Старт команды /stats — только для админов
async def start_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 У вас нет прав для использования этой команды.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(s["name"], callback_data=str(i))]
        for i, s in enumerate(SERVERS)
    ]
    await update.message.reply_text(
        "🖥️ Выберите сервер для просмотра игроков:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_SERVER

# 📊 Обработка выбора сервера
async def handle_stats_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data)
    server = SERVERS[index]

    try:
        response = requests.get(
            f"{server['url']}/api/player/",
            auth=server['auth'],
            timeout=10
        )
        data = response.json()
        players = data.get("data", {}).get("players", [])

        if not players:
            await query.message.reply_text(f"👥 *{server['name']}* — никто не онлайн", parse_mode="Markdown")
            return ConversationHandler.END

        lines = []
        for p in players:
            kills = p.get("kills", {})
            banned = p.get("banned", {})
            position = p.get("position", {})
            pos_str = f"{position.get('x','—')}, {position.get('y','—')}, {position.get('z','—')}"
            ip = p.get("ip", "—")
            ip_info = get_ip_info(ip)

            lines.append(
                f"👤 `{p.get('name','?')}`\n"
                f"🆔 EntityID: `{p.get('entityId','—')}`\n"
                f"🎮 SteamID: `{p.get('platformId',{}).get('userId','—')}`\n"
                f"🌐 IP: `{ip}`\n"
                f"📌 Регион: {ip_info}\n"
                f"📍 Позиция: `{pos_str}`\n"
                f"📶 Пинг: `{p.get('ping','—')}` | ❤️ `{p.get('health','—')}` | ⚡ `{p.get('stamina','—')}`\n"
                f"📈 Уровень: `{p.get('level','—')}` | 💀 Смерти: `{p.get('deaths','—')}`\n"
                f"🧟 Зомби: `{kills.get('zombies',0)}` | 👥 Игроков: `{kills.get('players',0)}`\n"
                f"🚫 Бан: `{banned.get('banActive', False)}`\n----"
            )

        chunk_size = 10
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            chunk_text = f"👥 *{server['name']}* — онлайн ({len(players)}):\n\n" + "\n".join(chunk)

            try:
                await query.message.reply_text(chunk_text, parse_mode="Markdown")
            except TelegramError as e:
                if "Message is too long" in str(e):
                    file = BytesIO()
                    file.write(chunk_text.encode('utf-8'))
                    file.seek(0)
                    await query.message.reply_document(file, filename=f"{server['name']}_stats_{i//chunk_size+1}.txt")
                else:
                    await query.message.reply_text(f"❌ Ошибка при отправке: `{e}`", parse_mode="Markdown")

    except Exception as e:
        await query.message.reply_text(f"❌ *{server['name']}* — ошибка: `{e}`", parse_mode="Markdown")

    return ConversationHandler.END

# 📦 Экспорт хендлера
stats_handler = ConversationHandler(
    entry_points=[CommandHandler("stats", start_stats)],
    states={SELECT_SERVER: [CallbackQueryHandler(handle_stats_server)]},
    fallbacks=[]
)

stats_handlers = [stats_handler]
