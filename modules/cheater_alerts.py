import requests
import time
import re
import threading
from config import TOKEN, GROUP_CHAT_ID, CHANNEL_CHAT_ID, SERVERS

CHEAT_KEYWORDS = ["чит", "читак", "читер", "читеры", "читами", "читов"]

# 🔍 Проверка сообщения на ключевые слова
def contains_cheat_word(msg):
    return any(word in msg.lower() for word in CHEAT_KEYWORDS)

# 📤 Отправка алерта в Telegram (только в группу и канал)
def send_cheater_alert(msg, server_name):
    alert = (
        f"⚠️ Обнаружено сообщение с подозрением на чит\n"
        f"🖥️ Сервер: {server_name}\n"
        f"💬 Текст: {msg}"
    )

    recipients = [GROUP_CHAT_ID, CHANNEL_CHAT_ID]

    for chat_id in recipients:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": alert},
                timeout=5
            ).raise_for_status()
        except Exception as e:
            print(f"❌ Не удалось отправить в {chat_id}: {e}")

# 🔄 Слушатель логов
def run_cheater_listener(server):
    print(f"🛡️ Запуск мониторинга 'чит' для {server['name']}")
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

    # 🎯 Обрабатываем только настоящие игровые сообщения от Steam
    if "Chat (from 'Steam_" not in msg:
        continue

    # 🚫 Игнорируем сообщения, обработанные модами
    if "Chat handled by mod" in msg:
        continue

    if contains_cheat_word(msg):
        send_cheater_alert(msg, server["name"])


        time.sleep(5)

# 🚀 Запуск всех слушателей
def start_cheater_alerts():
    for server in SERVERS:
        threading.Thread(target=run_cheater_listener, args=(server,), daemon=True).start()
