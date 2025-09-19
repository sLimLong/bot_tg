from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def admin_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
    "🛠 <b>Админ-меню</b>\n\n"
    "📋 <b>Статистика и игроки</b>\n"
    "/stats — общая статистика сервера\n"
    "/top_players — топ игроков по онлайну\n"
    "/top_voters — топ голосующих\n"
    "/players — список онлайн игроков\n\n"
    "🧹 <b>Кик/Бан</b>\n"
    "/kick [имя] — кикнуть игрока\n"
    "/ban [имя] — забанить игрока\n"
    "/banlist_alpha — банлист сервера Alpha\n"
    "/banlist_bravo — банлист сервера Bravo\n"
    "/banlist_charlie — банлист сервера Charlie\n\n"
    "🔧 <b>Служебные</b>\n"
    "/amenu — показать это меню\n"
    "/reset_stats — сбросить статистику\n"
    "/bloodmoon — информация о ближайшей орде\n"
    "/reload_config - Обновление конфигураций бота\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")

admin_menu_handler = CommandHandler("amenu", admin_menu_command)
