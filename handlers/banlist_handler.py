from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from modules.banlist import update_banlist

def update_banlist_command(update: Update, context: CallbackContext):
    update.message.reply_text("🔄 Обновляю банлист...")
    update_banlist(context)
    update.message.reply_text("✅ Банлист обновлён.")

def register_banlist_handler(dispatcher):
    dispatcher.add_handler(CommandHandler("updatebanlist", update_banlist_command))
