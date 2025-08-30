# kickban.py
import telnetlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from config import SERVERSRCON as SERVERS

# 🎯 Состояния
KICK_SELECT, KICK_ID = range(2)
BAN_SELECT, BAN_STEAMID, BAN_REASON, BAN_DAYS = range(2, 6)
BANALL_STEAMID, BANALL_REASON, BANALL_DAYS = range(6, 9)

# 🔧 Отправка команды
def send_command(server, command: str):
    host = server["host"]
    port = server["port"]
    password = server["password"]

    print(f"🔌 Подключение к {host}:{port}")
    try:
        tn = telnetlib.Telnet(host, port, timeout=5)
        tn.read_until(b"Please enter password:")
        tn.write(password.encode("ascii") + b"\n")
        tn.write(command.encode("ascii") + b"\n")
        tn.write(b"exit\n")
        response = tn.read_all().decode("cp1251", errors="ignore")
        print(f"📄 Ответ: {response.strip()}")
        return 200, response.strip()
    except Exception as e:
        print(f"❌ Ошибка Telnet: {e}")
        return None, str(e)



# 📦 Формат результата
def format_result(server_name, status, response, success_text):
    if status == 200:
        return f"✅ {server_name}: {success_text}"
    elif status:
        return f"⚠️ {server_name}: ошибка {status} — {response}"
    else:
        return f"❌ {server_name}: исключение — {response}"

# 👢 Кик
def kick_player(entity_id: str, server_index: int):
    server = SERVERS[server_index]
    command = f"kick {entity_id}"
    status, response = send_command(server, command)
    return format_result(server["name"], status, response, "кикнут")

# 🚫 Бан
def ban_player(steam_id: str, reason: str, days: int, server_index: int):
    server = SERVERS[server_index]
    command = f"ban add Steam_{steam_id} {days} days {reason}"
    status, response = send_command(server, command)
    return format_result(server["name"], status, response, "забанен")

# 🚫 Бан на всех
def ban_on_all_servers(steam_id: str, reason: str, days: int):
    results = []
    for server in SERVERS:
        command = f"ban add Steam_{steam_id} {days} days {reason}"
        status, response = send_command(server, command)
        results.append(format_result(server["name"], status, response, "забанен"))
    return "\n".join(results)

# 👢 Диалог кика
async def start_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(s["name"], callback_data=str(i))] for i, s in enumerate(SERVERS)]
    await update.message.reply_text("🖥️ Выберите сервер для кика:", reply_markup=InlineKeyboardMarkup(keyboard))
    return KICK_SELECT

async def handle_kick_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["kick_server_index"] = int(query.data)
    await query.message.reply_text("🔢 Введите EntityID игрока для кика:")
    return KICK_ID

async def handle_kick_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entity_id = update.message.text.strip()
    index = context.user_data["kick_server_index"]
    result = kick_player(entity_id, index)
    await update.message.reply_text(result, parse_mode="Markdown")
    return ConversationHandler.END

# 🚫 Диалог бана
async def start_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(s["name"], callback_data=str(i))] for i, s in enumerate(SERVERS)]
    await update.message.reply_text("🖥️ Выберите сервер для бана:", reply_markup=InlineKeyboardMarkup(keyboard))
    return BAN_SELECT

async def handle_ban_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ban_server_index"] = int(query.data)
    await query.message.reply_text("🔢 Введите SteamID64 игрока:")
    return BAN_STEAMID

async def handle_ban_steamid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ban_steamid"] = update.message.text.strip()
    await update.message.reply_text("✍️ Введите причину бана:")
    return BAN_REASON

async def handle_ban_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ban_reason"] = update.message.text.strip()
    await update.message.reply_text("📅 Введите срок бана в днях:")
    return BAN_DAYS

async def handle_ban_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text.strip())
        steam_id = context.user_data["ban_steamid"]
        reason = context.user_data["ban_reason"]
        index = context.user_data["ban_server_index"]
        result = ban_player(steam_id, reason, days, index)
        await update.message.reply_text(result, parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ Введите число дней, например: 3")
        return BAN_DAYS
    return ConversationHandler.END

# 🚫 Диалог бана на всех
async def start_banall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔢 Введите SteamID64 игрока для бана на всех серверах:")
    return BANALL_STEAMID

async def handle_banall_steamid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["banall_steamid"] = update.message.text.strip()
    await update.message.reply_text("✍️ Введите причину бана:")
    return BANALL_REASON

async def handle_banall_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["banall_reason"] = update.message.text.strip()
    await update.message.reply_text("📅 Введите срок бана в днях:")
    return BANALL_DAYS

async def handle_banall_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        days = int(update.message.text.strip())
        steam_id = context.user_data["banall_steamid"]
        reason = context.user_data["banall_reason"]
        result = ban_on_all_servers(steam_id, reason, days)
        await update.message.reply_text(result, parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ Введите число дней, например: 3")
        return BANALL_DAYS
    return ConversationHandler.END

# ❌ Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END

# 📦 Экспорт хендлеров
kickban_handlers = [
    ConversationHandler(
        entry_points=[CommandHandler("kick", start_kick)],
        states={
            KICK_SELECT: [CallbackQueryHandler(handle_kick_server)],
            KICK_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_kick_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ),
    ConversationHandler(
        entry_points=[CommandHandler("ban", start_ban)],
        states={
            BAN_SELECT: [CallbackQueryHandler(handle_ban_server)],
            BAN_STEAMID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ban_steamid)],
            BAN_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ban_reason)],
            BAN_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ban_days)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ),
    ConversationHandler(
        entry_points=[CommandHandler("banall", start_banall)],
        states={
            BANALL_STEAMID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_banall_steamid)],
            BANALL_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_banall_reason)],
            BANALL_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_banall_days)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
]
