from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import ALLOWED_ADMINS  # список ID админов

async def admin_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ALLOWED_ADMINS:
        await update.message.reply_text("⛔️ У вас нет прав для использования этой команды.")
        return

    text = (
        "🛠 <b>Админ-меню</b>\n\n"
        "📋 <b>Статистика и игроки</b>\n"
        "/stats — общая статистика сервера\n"
        "/top_players — топ игроков по онлайну\n"
        "/top_voters — топ голосующих\n"
        "/sc — Отправка команды в консоль\n"
        "/players — список онлайн игроков\n\n"
        "🧹 <b>Кик/Бан</b>\n"
        "/kick [имя] — кикнуть игрока\n"
        "/ban [имя] — забанить игрока\n\n"
        "🔧 <b>Служебные</b>\n"
        "/amenu — показать это меню\n"
        "/updatebanlist — Обновить бан лист\n"
        "/syncbanlist — Синхронизировать бан лист\n"
        "/reset_stats — сбросить статистику\n"
        "/reload_config — обновление конфигураций бота\n"
        "/update_bot — обновление бота и рестарт\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")

admin_menu_handler = CommandHandler("amenu", admin_menu_command)
