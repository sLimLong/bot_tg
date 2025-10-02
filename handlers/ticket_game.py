import requests
import time
import re
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import TOKEN, SERVERS, TICKET_GROUP_ID, TICKET_THREAD_ID

# 📍 Получение позиции игрока через /api/player/
def get_player_position(player_name: str) -> str:
    for server in SERVERS:
        try:
            response = requests.get(
                f"{server['url']}/api/player/",
                auth=server['auth'],
                timeout=5
            )
            data = response.json()
            players = data.get("data", {}).get("players", [])
            for p in players:
                name = p.get("name", "")
                if name.lower() == player_name.lower():
                    pos = p.get("position", {})
                    return f"X:{pos.get('x','—')} Y:{pos.get('y','—')} Z:{pos.get('z','—')}"
        except Exception as e:
            print(f"❌ Ошибка получения позиции: {e}")
    print(f"⚠️ Позиция игрока '{player_name}' не найдена")
    return "Неизвестно"

# 📤 Отправка тикета в Telegram
def send_ticket(player_name: str, message: str, steam_id: str = None):
    coords = get_player_position(player_name)
    if coords == "Неизвестно" and steam_id:
        coords = f"SteamID: {steam_id}"

    text = (
        f"🎫 *Тикет от игрока:* `{player_name}`\n"
        f"📍 *Позиция:* `{coords}`\n"
        f"📝 *Сообщение:* _{message}_"
    )

    buttons = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"ticket_accept:{player_name}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"ticket_reject:{player_name}")
        ]
    ]

    payload = {
        "chat_id": TICKET_GROUP_ID,
        "message_thread_id": TICKET_THREAD_ID,
        "text": text,
        "reply_markup": InlineKeyboardMarkup(buttons).to_dict(),
        "parse_mode": "Markdown"
    }

    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=payload, timeout=5).raise_for_status()
        print(f"📨 Тикет отправлен: {player_name}")
    except Exception as e:
        print(f"❌ Ошибка отправки тикета: {e}")

# 🔄 Слушатель логов
def run_ticket_listener(server):
    print(f"🎫 Запуск тикет-мониторинга для {server['name']}")
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
            time.sleep(120)
            continue

        for entry in entries:
            last_line = entry.get("id", last_line)
            msg = entry.get("msg", "")

            if "Chat (from 'Steam_" not in msg or "Chat handled by mod" in msg:
                continue

            if "/ahelp " in msg:
                match = re.search(
                    r"Chat \(from 'Steam_(\d{17})', entity id '\d+', to 'Global'\): '([^']+)':\s*/ahelp (.+)",
                    msg
                )
                if match:
                    steam_id, player_name, help_text = match.groups()
                    print(f"📨 Тикет от {player_name}: {help_text}")
                    send_ticket(player_name, help_text, steam_id)

        time.sleep(120)

# 🚀 Запуск всех слушателей
def start_ticket_monitoring():
    for server in SERVERS:
        threading.Thread(target=run_ticket_listener, args=(server,), daemon=True).start()
