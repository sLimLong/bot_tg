import telnetlib
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from config import SERVERSRCON, ALLOWED_ADMINS

# Временное хранилище выбора сервера
pending_server_selection = {}

def send_telnet_command(server, command):
    try:
        tn = telnetlib.Telnet(server["host"], server["port"], timeout=5)
        tn.read_until(b"Please enter password:", timeout=3)
        tn.write(server["password"].encode("utf-8") + b"\n")
        tn.write(command.encode("utf-8") + b"\n")
        output = tn.read_until(b">", timeout=5).decode("utf-8")
        tn.write(b"exit\n")
        return output.strip()
    except Exception as e:
        logging.warning(f"[telnet] {server['name']} — ошибка: {e}")
        return f"❌ Ошибка: {e}"

async def shell_command_entry(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_ADMINS:
        await update.message.reply_text("⛔ У вас нет прав на выполнение этой команды.")
        return

    keyboard = [
        [InlineKeyboardButton(server["name"], callback_data=f"sc_select:{server['name']}")]
        for server in SERVERSRCON
    ]
    await update.message.reply_text("🖥 Выберите сервер:", reply_markup=InlineKeyboardMarkup(keyboard))

async def shell_server_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    server_name = query.data.split(":")[1]
    pending_server_selection[user_id] = server_name

    await query.message.reply_text(f"💬 Введите команду для сервера <b>{server_name}</b>:", parse_mode="HTML")

async def shell_command_received(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_ADMINS or user_id not in pending_server_selection:
        return

    server_name = pending_server_selection.pop(user_id)
    command = update.message.text

    server = next((s for s in SERVERSRCON if s["name"] == server_name), None)
    if not server:
        await update.message.reply_text(f"❌ Сервер '{server_name}' не найден.")
        return

    result = send_telnet_command(server, command)
    await update.message.reply_text(f"📤 Ответ от <b>{server_name}</b>:\n<pre>{result}</pre>", parse_mode="HTML")

def register_shell_command(app):
    app.add_handler(CommandHandler("sc", shell_command_entry))
    app.add_handler(CallbackQueryHandler(shell_server_selected, pattern=r"^sc_select:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, shell_command_received))
