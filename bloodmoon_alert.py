import time
import logging
import requests
from telegram import Bot
from telegram.ext import CallbackContext, JobQueue

from config import SERVERS  # список серверов с name, url, auth

# 🧩 Настройки топиков для каждого сервера
GROUPS = {
    "7DTD PVE 1": {"chat_id": -1002695272288, "thread_id": 6},
    "7DTD PVE 2": {"chat_id": -1002695272288, "thread_id": 4},
    "7DTD PVE 3": {"chat_id": -1002695272288, "thread_id": 8}
}

# ⏱ Интервал между оповещениями (в секундах)
BLOODMOON_INTERVAL = 3600  # 1 час
last_bloodmoon_alert = {}

# 🔍 Проверка КН на серверах
async def check_bloodmoon(context: CallbackContext):
    bot: Bot = context.bot
    servers = context.job.data

    logging.info("[bloodmoon] Запуск проверки КН...")

    for server in servers:
        name = server.get("name")
        group = GROUPS.get(name)
        if not group:
            logging.warning(f"[bloodmoon] Нет настроек для {name}")
            continue

        key = (name, "bloodmoon")
        now = time.time()
        if now - last_bloodmoon_alert.get(key, 0) < BLOODMOON_INTERVAL:
            continue

        try:
            response = requests.get(f"{server['url']}/api/getstats", auth=server['auth'], timeout=5)
            data = response.json()
            day = data.get("gametime", {}).get("days")

            if not isinstance(day, int):
                logging.warning(f"[bloodmoon] Некорректный день на {name}: {day}")
                continue

            if day % 7 == 0:
                msg = f"🌕 Сегодня — Красная ночь на сервере {name}! Сейчас День {day}."
            elif day % 7 == 6:
                msg = f"🩸 Завтра — Красная ночь на сервере {name}! Сейчас День {day}."
            else:
                msg = None

            if msg:
                await bot.send_message(chat_id=group["chat_id"], text=msg)
                await bot.send_message(chat_id=group["chat_id"], message_thread_id=group["thread_id"], text=msg)
                last_bloodmoon_alert[key] = now
                logging.info(f"[bloodmoon] Оповещение отправлено: {msg}")

        except Exception as e:
            logging.warning(f"[bloodmoon] Ошибка на {name}: {e}")

# 🚀 Запуск задачи
def schedule_bloodmoon_jobs(job_queue: JobQueue):
    job_queue.run_repeating(
        callback=check_bloodmoon,
        interval=300,
        first=5,
        data=SERVERS
    )
