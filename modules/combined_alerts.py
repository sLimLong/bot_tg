import requests
import time
import re
import threading
from config import TOKEN, GROUP_CHAT_ID, CHANNEL_CHAT_ID, SERVERS

# 🔍 Регулярки
STAMINA_REGEX = re.compile(
    r"WRN Detected id 'Steam_(\d+)' 'EOS_([a-f0-9]+)' named '([^']+)' with an illegal stamina value of '(\d+)'"
)
HEALTH_REGEX = re.compile(
    r"WRN Detected id 'Steam_(\d+)' 'EOS_([a-f0-9]+)' named '([^']+)' with an illegal health value of '(\d+)'"
)
LEVEL_JUMP_REGEX = re.compile(
    r"WARNING: ([^\(]+) \(Steam_(\d+)\) jumped up more than one level \((\d+) -> (\d+)\)"
)
CHEAT_KEYWORDS = ["читак", "читер", "читеры", "читами", "читов", "сломали"]

# 📤 Унифицированная отправка алерта
def send_alert(text):
    recipients = [
        {"chat_id": GROUP_CHAT_ID, "message_thread_id": CHANNEL_CHAT_ID}
    ]
    for recipient in recipients:
        try:
            payload = {"text": text, **recipient}
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json=payload,
                timeout=5
            ).raise_for_status()
        except Exception as e:
            print(f"❌ Не удалось отправить в {recipient}: {e}")

# 📌 Нарушение по stamina/health
def handle_stat_violation(msg, server_name):
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
        f"🚨 Нарушение по {stat_type}!\n"
        f"🖥️ Сервер: {server_name}\n"
        f"👤 Игрок: {player_name}\n"
        f"🎮 SteamID: {steam_id}\n"
        f"🧬 EOS: {eos_id}\n"
        f"{emoji} Значение: {value}"
    )
    send_alert(alert)

# 📌 Прыжок уровня
def handle_level_jump(msg, server_name):
    match = LEVEL_JUMP_REGEX.search(msg)
    if not match:
        return

    player_name, steam_id, old_level, new_level = match.groups()
    old_level = int(old_level)
    new_level = int(new_level)

    if new_level - old_level <= 5:
        return

    alert = (
        f"📈 Подозрительный прыжок уровня!\n"
        f"🖥️ Сервер: {server_name}\n"
        f"👤 Игрок: {player_name}\n"
        f"🎮 SteamID: {steam_id}\n"
        f"📊 Уровень: {old_level} → {new_level}"
    )
    send_alert(alert)

# 📌 Читерские сообщения
def handle_cheater_chat(msg, server_name):
    if any(word in msg.lower() for word in CHEAT_KEYWORDS):
        alert = (
            f"⚠️ Обнаружено сообщение\n"
            f"🖥️ Сервер: {server_name}\n"
            f"💬 Текст: {msg}"
        )
        send_alert(alert)

# 🔄 Слушатель логов
def run_combined_listener(server):
    print(f"🔍 Запуск мониторинга для {server['name']}")
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
                handle_stat_violation(msg, server["name"])

            elif "[CSMM_Patrons] WARNING:" in msg and "jumped up more than one level" in msg:
                handle_level_jump(msg, server["name"])

            elif "Chat (from 'Steam_" in msg and "Chat handled by mod" not in msg:
                handle_cheater_chat(msg, server["name"])

        time.sleep(5)

# 🚀 Запуск всех слушателей
def start_combined_alerts():
    for server in SERVERS:
        threading.Thread(target=run_combined_listener, args=(server,), daemon=True).start()
