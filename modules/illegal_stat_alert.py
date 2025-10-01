import requests
import time
import re
import threading
from config import TOKEN, GROUP_CHAT_ID, CHANNEL_CHAT_ID, SERVERS

# 🔍 Регулярки для нарушений
STAMINA_REGEX = re.compile(
    r"WRN Detected id 'Steam_(\d+)' 'EOS_([a-f0-9]+)' named '([^']+)' with an illegal stamina value of '(\d+)'"
)

HEALTH_REGEX = re.compile(
    r"WRN Detected id 'Steam_(\d+)' 'EOS_([a-f0-9]+)' named '([^']+)' with an illegal health value of '(\d+)'"
)

# 📤 Отправка алерта
def send_stat_alert(msg, server_name):
    match_stamina = STAMINA_REGEX.search(msg)
    match_health = HEALTH_REGEX.search(msg)

    if match_stamina:
        steam_id, eos_id, player_name, value = match_stamina.groups()
        stat_type = "stamina"
        emoji = "💥"
    elif match_health:
        steam_id, eos_id, player_name, value = match_health.groups()
        stat_type = "health"
        emoji = "❤️"
    else:
        return

    alert = (
        f"🚨 Обнаружено нарушение по {stat_type}!\n"
        f"🖥️ Сервер: {server_name}\n"
        f"👤 Игрок: {player_name}\n"
        f"🎮 SteamID: {steam_id}\n"
        f"🧬 EOS: {eos_id}\n"
        f"{emoji} Значение {stat_type}: {value}"
    )

    recipients = [
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
def run_stat_listener(server):
    print(f"🧪 Запуск мониторинга stamina/health для {server['name']}")
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

            if "WRN Detected" in msg and ("illegal stamina value" in msg or "illegal health value" in msg):
                send_stat_alert(msg, server["name"])

        time.sleep(5)

# 🚀 Запуск всех слушателей
def start_stat_alerts():
    for server in SERVERS:
        threading.Thread(target=run_stat_listener, args=(server,), daemon=True).start()
