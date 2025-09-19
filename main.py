import logging
from telegram.ext import ApplicationBuilder
from config import TOKEN

# 👥 Импорт хендлеров
from players import players_handler, players_callback_handler
from admin import admin_handlers
from status import status_handlers, schedule_jobs
from kickban import kickban_handlers
from stats import stats_handler
from top_voters import top_voters_handler, top_voters_callback_handler
from top_players import top_players_handler, top_players_callback_handler, reset_stats_handler
from specific_topic_to_vk import topic_handler 
from bloodmoon_alert import schedule_bloodmoon_jobs


# 🔧 Логирование в консоль
logging.basicConfig(level=logging.INFO)

def run_bot():
    logging.info("✅ Бот запускается...")

    try:
        app = ApplicationBuilder().token(TOKEN).build()

        # 📦 Группировка хендлеров
        core_handlers = admin_handlers + status_handlers + kickban_handlers
        stats_handlers = [stats_handler]
        voters_handlers = [top_voters_handler, top_voters_callback_handler]
        players_handlers = [players_handler, players_callback_handler]
        top_players_handlers = [top_players_handler, top_players_callback_handler, reset_stats_handler]
        vk_handlers = [topic_handler]

        # 📥 Регистрируем все хендлеры
        all_handlers = (
            core_handlers +
            stats_handlers +
            voters_handlers +
            players_handlers +
            top_players_handlers +
            vk_handlers
        )

        for handler in all_handlers:
            app.add_handler(handler)

        # ⏱ Фоновые задачи
        schedule_bloodmoon_jobs(app.job_queue)

        logging.info("✅ Все модули подключены. Ожидаем события...")
        app.run_polling()

    except Exception as e:
        logging.error(f"❌ Ошибка при запуске: {e}")

if __name__ == "__main__":
    run_bot()
