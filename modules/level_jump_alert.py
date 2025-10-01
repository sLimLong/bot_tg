import requests
import time
import re
import threading
from config import TOKEN, GROUP_CHAT_ID, CHANNEL_CHAT_ID  # CHANNEL_CHAT_ID — это thread_id
from config import SERVERS

# 🔍 Регулярка для прыжка уровня
LEVEL_JUMP_REGEX = re.compile(
    r"

\[CSMM_Patrons\]

 WARNING: (.+?) \(Steam_(\d+)\) jumped up more than one level \((\d+) -> (\d+)\)"
)

# 📤 Отправка алерта в Telegram
def send_level_jump_alert(msg, server_name):
    match = LEVEL_JUMP_REGEX.search(msg)
    if not match:
        return

    player_name, steam_id, old_level, new_level = match.groups()

    alert = (
        f"📈 Подозрительный прыжок уровня!\n"
        f"🖥️ Сервер: {server_name}\n"
        f"👤 Игрок: {player_name}\n"
        f"🎮 SteamID: {steam_id}\n"
        f"📊 Уровень: {old_level} → {new_level}"
    )

    recipients = [
        {"chat_id": GROUP_CHAT_ID},
        {"chat_id": GROUP_CHAT_ID, "message_thread_id": CHANNEL_CHAT_ID}
    ]

    for recipient in recipients:
        try:
            payload = {"text": alert, **recipient}
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json=payload,
                timeout=5
            ).raise_for_status()
        except Exception as e:
            print(f"❌ Не удалось отправить в {recipient}: {e}")

# 🔄 Слушатель логов
def run_level_jump_listener(server):
    print(f"📡 Запуск мониторинга прыжков уровня для {server['name']}")
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

            if "[CSMM_Patrons] WARNING:" in msg and "jumped up more than one level" in msg:
                send_level_jump_alert(msg, server["name"])

        time.sleep(5)

# 🚀 Запуск всех слушателей
def start_level_jump_alerts():
    for server in SERVERS:
        threading.Thread(target=run_level_jump_listener, args=(server,), daemon=True).start()
