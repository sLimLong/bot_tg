import logging
from telegram.ext import ApplicationBuilder
from config import TOKEN
from players import players_handler
from admin import admin_handlers
from status import status_handlers, schedule_jobs
from quest import quest_handlers
from apl import apl_handlers
from kickban import kickban_handlers

# 🔧 Логирование только в консоль
logging.basicConfig(level=logging.INFO)

def run_bot():
    logging.info("✅ Бот запускается...")

    try:
        app = ApplicationBuilder().token(TOKEN).build()

        # Подключаем все хендлеры
        all_handlers = (
            admin_handlers +
            status_handlers +
            quest_handlers +
            apl_handlers +
            kickban_handlers +
            [players_handler]
        )
        for handler in all_handlers:
            app.add_handler(handler)

        # Запускаем фоновую задачу (если есть)
        schedule_jobs(app)

        logging.info("✅ Все модули подключены. Ожидаем события...")
        app.run_polling()

    except Exception as e:
        logging.error(f"❌ Ошибка при запуске: {e}")

if __name__ == "__main__":
    run_bot()
