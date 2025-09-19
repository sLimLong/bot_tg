import json
import os
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

BANLIST_PATH = os.path.join("data", "banlist.json")

def load_banlist():
    if not os.path.exists(BANLIST_PATH):
        return {}
    try:
        with open(BANLIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {}

async def whois_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажите имя или SteamID: /whois Darkin_m")
        return

    query = " ".join(context.args).strip().lower()
    banlist = load_banlist()
    result = [f"🔍 Поиск: <b>{query}</b>\n"]
    found = False

    for server, entries in banlist.items():
        for entry in entries:
            name = entry.get("name", "").lower()
            steamid = entry.get("steamid", "").lower()
            if query in name or query in steamid:
                result.append(
                    f"🛑 <b>{server}</b>\n"
                    f"👤 {entry['name']} ({entry['steamid']})\n"
                    f"⏳ До: {entry['date']}\n"
                    f"📄 Причина: {entry['reason']}\n"
                )
                found = True

    if not found:
        result.append("✅ Не найден в банлистах.")

    await update.message.reply_text("\n".join(result), parse_mode="HTML")

whois_handler = CommandHandler("whois", whois_command)
