import time
import logging
import requests
from telegram import Bot
from telegram.ext import CallbackContext, JobQueue
from config import SERVERS, GROUPS, BLOODMOON_INTERVAL
from config import ALLOWED_ADMINS

last_bloodmoon_alert = {}

async def force_bloodmoon(update, context):
    user_id = update.effective_user.id

    if user_id not in ALLOWED_ADMINS:
        await update.message.reply_text("⛔ У вас нет прав для выполнения этой команды.")
        return

    await update.message.reply_text("🔄 Принудительная проверка КН запущена.")

    # Запускаем стандартную функцию check_bloodmoon как разовую задачу
    context.job_queue.run_once(
        callback=check_bloodmoon,
        when=0,
        data=SERVERS
    )


# 🔍 Проверка КН на серверах
async def check_bloodmoon(context: CallbackContext):
    bot: Bot = context.bot
    servers = context.job.data

    logging.info("[bloodmoon] Запуск проверки КН...")

    for server in servers:
        name = server.get("name", "").strip()
        group = GROUPS.get(name)

        if not group:
            logging.warning(f"[bloodmoon] Нет настроек для сервера: {name}")
            continue

        key = (name, "bloodmoon")
        now = time.time()

        # ⏳ Проверка интервала
        if now - last_bloodmoon_alert.get(key, 0) < BLOODMOON_INTERVAL:
            logging.info(f"[bloodmoon] Пропуск {name} — интервал не истёк")
            continue

        try:
            response = requests.get(f"{server['url']}/api/getstats", auth=server['auth'], timeout=5)
            data = response.json()
            day = data.get("gametime", {}).get("days")
            hours = data.get("gametime", {}).get("hours")
            minutes = data.get("gametime", {}).get("minutes")


            logging.info(f"[bloodmoon] Сервер {name} — День {day}")
            time_str = f"{hours:02d}:{minutes:02d}"

            if not isinstance(day, int):
                logging.warning(f"[bloodmoon] Некорректный формат дня на {name}: {day}")
                continue

            if day % 7 == 0:
                msg = f"🌕 Сегодня — Красная ночь на сервере {name}! Сейчас День {day}, Время {time_str}"
            elif day % 7 == 6:
                msg = f"🩸 Завтра — Красная ночь на сервере {name}! Сейчас День {day}, Время {time_str}"
            else:
                logging.info(f"[bloodmoon] Нет КН на {name} — День {day}, Время {time_str}")
                continue

            # 📤 Отправка в топик
            await bot.send_message(
                chat_id=group["chat_id"],
                message_thread_id=group["thread_id"],
                text=msg
            )

            last_bloodmoon_alert[key] = now
            logging.info(f"[bloodmoon] Оповещение отправлено на {name}: {msg}")

        except Exception as e:
            logging.warning(f"[bloodmoon] Ошибка на {name}: {e}")

# 🚀 Запуск задачи
def schedule_bloodmoon_jobs(job_queue: JobQueue):
    logging.info("[bloodmoon] Планировщик активирован")
    job_queue.run_repeating(
        callback=check_bloodmoon,
        interval=300,  # каждые 5 минут
        first=5,
        data=SERVERS
    )

