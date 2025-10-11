import telnetlib
import re
import json
import os
import logging
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from config import SERVERSRCON, BANLIST_GROUP_ID, BANLIST_THREAD_ID
from collections import defaultdict

def fetch_banlist(server):
    try:
        tn = telnetlib.Telnet(server["host"], server["port"], timeout=5)
        tn.read_until(b"Please enter password:", timeout=3)
        tn.write(server["password"].encode("utf-8") + b"\n")
        tn.write(b"ban list\n")
        raw = tn.read_until(b">", timeout=5).decode("utf-8")
        tn.write(b"exit\n")

        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\S+) \((.*?)\) - (.+)"
        matches = re.findall(pattern, raw)

        return [
            {
                "date": date,
                "steamid": userid,
                "name": name,
                "reason": reason
            }
            for date, userid, name, reason in matches
        ]
    except Exception as e:
        logging.warning(f"[banlist] {server['name']} — ошибка: {e}")
        return []

async def notify_new_bans(context: CallbackContext, new_bans):
    # Группируем баны по серверу
    grouped = defaultdict(list)
    for server, entry in new_bans:
        grouped[server].append(entry)

    for server_name, entries in grouped.items():
        msg = f"🛑 Новые баны на сервере <b>{server_name}</b> ({len(entries)}):\n\n"
        for entry in entries:
            msg += (
                f"👤 {entry['name']} ({entry['steamid']})\n"
                f"📄 Причина: {entry['reason']}\n"
                f"⏳ До: {entry['date']}\n\n"
            )

        try:
            await context.bot.send_message(
                chat_id=BANLIST_GROUP_ID,
                message_thread_id=BANLIST_THREAD_ID,
                text=msg.strip(),
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"[banlist] Ошибка отправки банов для {server_name}: {e}")

async def update_banlist(context: CallbackContext = None):
    new_bans_total = []

    for server in SERVERSRCON:
        server_name = server["name"]
        new_entries = fetch_banlist(server)

        # Пути к файлам для конкретного сервера
        new_path = os.path.join("data", f"banlist_{server_name}.json")
        old_path = os.path.join("data", f"banlist_old_{server_name}.json")

        # Загружаем старые данные
        old_entries = []
        if os.path.exists(new_path):
            try:
                with open(new_path, "r", encoding="utf-8") as f:
                    old_entries = json.load(f)
            except Exception as e:
                logging.warning(f"[banlist] Ошибка чтения {new_path}: {e}")

        # Сохраняем новые и старые данные
        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(new_entries, f, indent=2, ensure_ascii=False)

        with open(old_path, "w", encoding="utf-8") as f:
            json.dump(old_entries, f, indent=2, ensure_ascii=False)

        # Сравниваем и накапливаем новые баны
        old_ids = {e["steamid"] for e in old_entries}
        for entry in new_entries:
            if entry["steamid"] not in old_ids:
                new_bans_total.append((server_name, entry))

    logging.info("[banlist] Банлист обновлён.")

    if context and new_bans_total:
        logging.info(f"[banlist] Отправляю {len(new_bans_total)} новых банов в чат.")
        await notify_new_bans(context, new_bans_total)

async def update_banlist_command(update: Update, context: CallbackContext):
    await update.message.reply_text("🔄 Обновляю банлист...")
    await update_banlist(context)
    await update.message.reply_text("✅ Банлист обновлён.")

def register_banlist_handler(app):
    app.add_handler(CommandHandler("updatebanlist", update_banlist_command))
