import requests
from collections import defaultdict
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# 🔐 API-ключи WarGM по серверам
SERVER_KEYS = {
    68433: "1sGAs_S_qsdA_h3PUPxMOfzJObAwI3lE",
    71764: "fqbJ86k_5_XJ_TBYdSV_I0ib2iGD8ghb",
    75803: "1sGAs_S_qsdA_h3PUPxMOfzJObAwI3lE"
}

# 🔑 Steam Web API ключ (получить на https://steamcommunity.com/dev/apikey)
STEAM_API_KEY = "FB274C66E6D5713BE04B2ACED448939D"

def fetch_voters_from_all_servers(limit=10):
    combined = defaultdict(lambda: {"votes": 0, "points": 0, "user_steam_id": ""})
    date_end = datetime.utcnow().date()
    date_start = date_end - timedelta(days=30)

    for server_id, key in SERVER_KEYS.items():
        url = (
            f"https://api.wargm.ru/v1/server/voters?"
            f"client={server_id}:{key}"
            f"&date_start={date_start}&date_end={date_end}"
        )
        try:
            response = requests.get(url)
            data = response.json()
            users = data.get("responce", {}).get("data", {})

            for user in users.values():
                sid = str(user.get("user_steam_id", "unknown"))
                combined[sid]["votes"] += user.get("votes", 0)
                combined[sid]["points"] += user.get("points", 0)
                combined[sid]["user_steam_id"] = sid
        except Exception as e:
            print(f"❌ Ошибка при запросе сервера {server_id}: {e}")

    top = sorted(combined.values(), key=lambda x: x["votes"], reverse=True)[:limit]
    return top

def fetch_steam_names(steam_ids):
    if not steam_ids:
        return {}

    steam_id_str = ",".join(steam_ids)
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id_str}"
    try:
        response = requests.get(url)
        data = response.json()
        players = data.get("response", {}).get("players", [])
        return {p["steamid"]: p.get("personaname", p["steamid"]) for p in players}
    except Exception as e:
        print(f"❌ Ошибка Steam API: {e}")
        return {}

def build_message(voters):
    if not voters:
        return "😕 За последний месяц никто не голосовал."

    steam_ids = [v["user_steam_id"] for v in voters if v["user_steam_id"] != "unknown"]
    steam_names = fetch_steam_names(steam_ids)

    message = "📅 Топ голосующих за последний месяц:\n"
    for i, user in enumerate(voters, 1):
        sid = user["user_steam_id"]
        name = steam_names.get(sid, f"SteamID: {sid}")
        votes = user["votes"]
        points = user["points"]
        profile_link = f"https://steamcommunity.com/profiles/{sid}"
        message += f"{i}. [{name}]({profile_link}) — {votes} голосов, {points} очков\n"
    return message

def build_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data="refresh")],
        [InlineKeyboardButton("📊 Топ 20", callback_data="top20")]
    ])

async def top_voters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voters = fetch_voters_from_all_servers(limit=10)
    message = build_message(voters)
    await update.message.reply_text(message, reply_markup=build_keyboard(), parse_mode="Markdown")

async def top_voters_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    limit = 20 if query.data == "top20" else 10
    voters = fetch_voters_from_all_servers(limit=limit)
    message = build_message(voters)
    await query.edit_message_text(message, reply_markup=build_keyboard(), parse_mode="Markdown")

# Хендлеры для main.py
top_voters_handler = CommandHandler("topvoters", top_voters_command)
top_voters_callback_handler = CallbackQueryHandler(top_voters_callback, pattern="^(refresh|top20)$")
