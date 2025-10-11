import telnetlib
import re
import os
import json
import time
import logging
from config import SERVERSRCON
from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
import asyncio

SYNC_PATH = os.path.join("data", "ban_sync.json")

def fetch_banlist(server):
    try:
        tn = telnetlib.Telnet(server["host"], server["port"], timeout=5)
        tn.read_until(b"Please enter password:", timeout=3)
        tn.write(server["password"].encode("utf-8") + b"\n")
        tn.write(b"ban list\n")
        raw = tn.read_until(b">", timeout=5).decode("utf-8", errors="ignore")
        tn.write(b"exit\n")

        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\S+) \((.*?)\) - (.+)"
        matches = re.findall(pattern, raw)

        banlist = []
        for date, steamid, name, reason in matches:
            banlist.append({
                "date": date,
                "steamid": steamid,
                "name": name if name != "-unknown-" else "unknown",
                "reason": reason
            })
        logging.info(f"[ban_sync] {server['name']}: загружено {len(banlist)} банов")
        return banlist
    except Exception as e:
        logging.warning(f"[ban_sync] Ошибка при получении банлиста с {server['name']}: {e}")
        return []

def send_ban(server, entry):
    try:
        tn = telnetlib.Telnet(server["host"], server["port"], timeout=5)
        tn.read_until(b"Please enter password:", timeout=3)
        tn.write(server["password"].encode("utf-8") + b"\n")

        auth_response = tn.read_until(b">", timeout=5).decode("utf-8", errors="ignore")
        logging.info(f"[ban_sync] Авторизация на {server['name']}: {auth_response}")

        try:
            ban_until = datetime.strptime(entry["date"], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            ban_days = max((ban_until - now).days, 1)
        except Exception:
            ban_days = 365

        # Обрезаем причину до 128 символов и гарантируем, что она целиком в кавычках
        reason = entry["reason"].strip()[:128].replace('"', '\\"')
        name = entry["name"].strip().split()[0].replace('"', '\\"')  # только ID

        cmd = f'ban add {entry["steamid"]} {ban_days} days "{reason}" "{name}"'

        logging.info(f"[ban_sync] Отправляю на {server['name']}: {cmd}")
        tn.write(cmd.encode("utf-8") + b"\n")

        time.sleep(1)
        response = tn.read_very_eager().decode("utf-8", errors="ignore")
        logging.info(f"[ban_sync] Ответ от {server['name']}: {response}")

        tn.write(b"exit\n")
    except Exception as e:
        logging.warning(f"[ban_sync] Ошибка при отправке на {server['name']}: {e}")

def sync_banlists():
    if len(SERVERSRCON) < 2:
        logging.warning("[ban_sync] Недостаточно серверов для синхронизации.")
        return

    all_banlists = {
        server["name"]: fetch_banlist(server)
        for server in SERVERSRCON
    }

    steamid_map = {}
    for server_name, bans in all_banlists.items():
        for entry in bans:
            steamid = entry["steamid"]
            if steamid not in steamid_map:
                steamid_map[steamid] = {"entry": entry, "servers": set()}
            steamid_map[steamid]["servers"].add(server_name)

    added_count = 0
    for steamid, data in steamid_map.items():
        for server in SERVERSRCON:
            name = server["name"]
            if name not in data["servers"]:
                send_ban(server, data["entry"])
                added_count += 1
                logging.info(f"[ban_sync] Бан {steamid} добавлен на {name}")

    with open(SYNC_PATH, "w", encoding="utf-8") as f:
        json.dump(all_banlists, f, indent=2, ensure_ascii=False)

    logging.info(f"[ban_sync] Синхронизация завершена. Добавлено {added_count} новых банов.")

async def sync_banlists_command(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text("🔄 Синхронизирую банлисты между серверами...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, sync_banlists)
        await update.message.reply_text("✅ Синхронизация завершена.")
    except Exception as e:
        logging.error(f"[ban_sync] Ошибка синхронизации: {e}")
        await update.message.reply_text("❌ Ошибка при синхронизации.")

def register_sync_command(app):
    app.add_handler(CommandHandler("syncbanlist", sync_banlists_command))
