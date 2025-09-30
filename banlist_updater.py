import telnetlib
import re
import json
import os
import logging
from config import SERVERSRCON, BANLIST_GROUP_ID, BANLIST_THREAD_ID

BANLIST_PATH = os.path.join("data", "banlist.json")
BANLIST_OLD_PATH = os.path.join("data", "banlist_old.json")

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

def update_banlist(context=None):
    new_data = {}
    for server in SERVERSRCON:
        new_data[server["name"]] = fetch_banlist(server)

    # Сравнение с предыдущим банлистом
    old_data = {}
    if os.path.exists(BANLIST_PATH):
        try:
            with open(BANLIST_PATH, "r", encoding="utf-8") as f:
                old_data = json.load(f)
        except Exception as e:
            logging.warning(f"[banlist] Ошибка чтения старого банлиста: {e}")

    # Сохраняем новый банлист
    with open(BANLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    # Сохраняем старый банлист для архива
    with open(BANLIST_OLD_PATH, "w", encoding="utf-8") as f:
        json.dump(old_data, f, indent=2, ensure_ascii=False)

    logging.info("[banlist] Банлист обновлён.")

    # 🔔 Уведомление о новых банах
    if context:
        new_bans = []
        for server, entries in new_data.items():
            old_entries = old_data.get(server, [])
            old_ids = {e["steamid"] for e in old_entries}
            for entry in entries:
                if entry["steamid"] not in old_ids:
                    new_bans.append((server, entry))

        if new_bans:
            msg = f"🛑 Обнаружено {len(new_bans)} новых банов:\n\n"
            for server, entry in new_bans[:10]:  # ограничим до 10
                msg += (
                    f"🌐 <b>{server}</b>\n"
                    f"👤 {entry['name']} ({entry['steamid']})\n"
                    f"📄 Причина: {entry['reason']}\n"
                    f"⏳ До: {entry['date']}\n\n"
                )

            context.bot.send_message(
                chat_id=BANLIST_GROUP_ID,
                message_thread_id=BANLIST_THREAD_ID,
                text=msg.strip(),
                parse_mode="HTML"
            )
