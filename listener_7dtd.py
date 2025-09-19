import requests
import time
import json
import re
import os
import asyncio
import threading
from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import SERVERS
from utils.registration import create_registration_code

PENDING_FILE = "data/pending_registrations.json"
LINKED_FILE = "data/linked_players.json"

# 📁 Файловые операции
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# 📦 Парсинг игровых логов
def parse_chat_log(msg):
    match = re.search(
        r"Chat \(from 'Steam_(\d{17})', entity id '\d+', to 'Global'\): '([^']+)':\s*/reg\s+([a-zA-Z0-9]{3,32})",
        msg
    )
    if match:
        return {
            "steamid": match.group(1),
            "player_name": match.group(2),
            "code": match.group(3)
        }
    return None

# 🔄 Основной listener
def run_listener(server, context):
    print(f"🚀 Запуск listener для {server['name']}")
    last_line = None

    headers = {
        "X-SDTD-API-TOKENNAME": server["auth"][0],
        "X-SDTD-API-SECRET": server["auth"][1],
        "User-Agent": "Mozilla/5.0"
    }

    while True:
        params = {"count": 50}
        if last_line is not None:
            params["firstLine"] = last_line + 1

        try:
            response = requests.get(f"{server['url']}/api/log", params=params, headers=headers, timeout=5)
            response.raise_for_status()
            entries = response.json().get("data", {}).get("entries", [])
        except Exception as e:
            print(f"❌ [{server['name']}] Ошибка получения логов: {e}")
            time.sleep(5)
            continue

        for entry in entries:
            last_line = entry.get("id", last_line)
            msg = entry.get("msg", "")
            if "/reg" not in msg:
                continue

            parsed = parse_chat_log(msg)
            if not parsed:
                continue

            steamid = parsed["steamid"]
            name = parsed["player_name"]
            code = parsed["code"]

            pending = load_json(PENDING_FILE)
            entry = pending.pop(code, None)
            save_json(PENDING_FILE, pending)

            telegram_id = entry["telegram_id"] if entry else None
            if not telegram_id:
                print(f"⚠️ [{server['name']}] Код {code} не найден")
                continue

            linked = load_json(LINKED_FILE)
            linked[f"Steam_{steamid}"] = {
                "server": server["name"],
                "telegram_id": telegram_id
            }
            save_json(LINKED_FILE, linked)

            print(f"🎉 [{server['name']}] {name} (Steam_{steamid}) ↔ Telegram ID {telegram_id}")

        time.sleep(5)

# 🚀 Запуск всех listener'ов
def run_all_listeners(context):
    for server in SERVERS:
        threading.Thread(target=run_listener, args=(server, context), daemon=True).start()

# 📲 Команда /reg в Telegram
async def handle_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    code = create_registration_code(user_id)

    pending = load_json(PENDING_FILE)
    pending[code] = {
        "telegram_id": user_id,
        "expires": datetime.utcnow().isoformat()
    }
    save_json(PENDING_FILE, pending)

    await update.message.reply_text(
        f"🔐 Ваш регистрационный код: <code>{code}</code>\n"
        f"Введите его в игре командой <code>/reg {code}</code>",
        parse_mode="HTML"
    )

reg_handler = CommandHandler("reg", handle_reg)

# 📲 Команда /whoami в Telegram
async def handle_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    linked = load_json(LINKED_FILE)

    matches = [k for k, v in linked.items() if v.get("telegram_id") == user_id]

    if not matches:
        await update.message.reply_text("❌ Вы не привязаны ни к одному Steam аккаунту.")
        return

    reply = "🔗 Ваша привязка:\n"
    for steam_key in matches:
        server = linked[steam_key]["server"]
        reply += f"• {steam_key} на сервере <b>{server}</b>\n"

    await update.message.reply_text(reply, parse_mode="HTML")

whoami_handler = CommandHandler("whoami", handle_whoami)
