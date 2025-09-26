import requests
import json
import os
from datetime import datetime
from config import SERVERS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ChatMemberStatus
from config import ALLOWED_ADMINS

DATA_FILE = os.path.join("data", "players_data.json")

def load_players_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_players_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("✅ Данные сохранены в players_data.json")
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")

def update_players_storage(new_players_by_server):
    data = load_players_data()
    now = datetime.utcnow().isoformat()

    for server_name, players in new_players_by_server.items():
        if server_name not in data:
            data[server_name] = {}

        for player in players:
            sid = player.get("steamid", player.get("name"))
            data[server_name][sid] = {
                "name": player.get("name", "Без имени"),
                "score": player.get("score", 0),
                "zombiekills": player.get("zombiekills", 0),
                "level": player.get("level", 0),
                "deaths": player.get("deaths", 0),
                "last_seen": now
            }

    save_players_data(data)

def fetch_player_data():
    all_players_by_server = {}

    for server in SERVERS:
        try:
            url = f"{server['url']}/api/player"
            response = requests.get(url, auth=server["auth"], timeout=10)
            data = response.json()
            players = data.get("data", {}).get("players", [])
            parsed_players = [{
                "name": p.get("name", "Без имени"),
                "steamid": p.get("platformId", {}).get("userId", ""),
                "score": p.get("score", 0),
                "zombiekills": p.get("kills", {}).get("zombies", 0),
                "level": p.get("level", 0),
                "deaths": p.get("deaths", 0)
            } for p in players]
            all_players_by_server[server["name"]] = parsed_players
        except Exception as e:
            print(f"❌ Ошибка при запросе к {server['name']}: {e}")
    return all_players_by_server


def calculate_total(player):
    return player["score"] + player["zombiekills"] + player["level"] - player["deaths"]

def build_top_message(data, key=None, label="общей активности", reverse=True, limit=10):
    if not data:
        return "😕 Нет данных о игроках."

    message = f"🏆 Топ игроков по {label}:\n\n"
    for server_name, players in data.items():
        message += f"🌐 Сервер: {server_name}\n"
        if key:
            sorted_players = sorted(players.values(), key=lambda x: x.get(key, 0), reverse=reverse)[:limit]
        else:
            sorted_players = sorted(players.values(), key=calculate_total, reverse=True)[:limit]

        for i, p in enumerate(sorted_players, 1):
            value = p.get(key, calculate_total(p)) if key else calculate_total(p)
            message += f"{i}. {p['name']} — {value}\n"
        message += "\n"
    return message


def build_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Общий топ", callback_data="total")],
        [InlineKeyboardButton("🎯 Счёт", callback_data="score"),
         InlineKeyboardButton("🧟 Зомби", callback_data="zombiekills")],
        [InlineKeyboardButton("📈 Уровень", callback_data="level"),
         InlineKeyboardButton("💀 Смерти", callback_data="deaths")]
    ])

async def top_players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    players = fetch_player_data()
    update_players_storage(players)
    data = load_players_data()
    message = build_top_message(data)
    await update.message.reply_text(message, reply_markup=build_keyboard())
    
async def top_players_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data
    label_map = {
        "score": "счёту",
        "zombiekills": "убийствам зомби",
        "level": "уровню",
        "deaths": "смертям",
        "total": "общей активности"
    }
    reverse = False if key == "deaths" else True
    key_for_sort = None if key == "total" else key

    data = load_players_data()
    message = build_top_message(data, key=key_for_sort, label=label_map[key], reverse=reverse)
    await query.edit_message_text(message, reply_markup=build_keyboard())
    
async def reset_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in ALLOWED_ADMINS:
        await update.message.reply_text("🚫 У вас нет прав на сброс статистики.")
        return

    save_players_data({})
    await update.message.reply_text("✅ Статистика игроков успешно сброшена.")
  
def update_players_job(context=None):
    players = fetch_player_data()
    update_players_storage(players)
    print("🔄 Игроки обновлены в players_data.json")

    

# Хендлеры для main.py
top_players_handler = CommandHandler("top_pl", top_players_command)
reset_stats_handler = CommandHandler("reset_stats", reset_stats_command)
top_players_callback_handler = CallbackQueryHandler(top_players_callback, pattern="^(score|zombiekills|level|deaths|total)$")


