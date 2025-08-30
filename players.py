# players.py

import requests, logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import SERVERS

# 👥 Команда /players — список игроков на всех серверах
async def players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = []

    for server in SERVERS:
        try:
            response = requests.get(
                f"{server['url']}/api/getplayersonline",
                auth=server['auth'],
                timeout=5
            )
            players = response.json()

            if not isinstance(players, list) or not players:
                messages.append(f"🖥️ {server['name']} — никто не онлайн")
                continue

            # Сортировка по имени
            players.sort(key=lambda p: p.get("name", "").lower())

            lines = [f"• {p.get('name', '?')}" for p in players]
            messages.append(f"🖥️ {server['name']} — онлайн ({len(players)}):\n" + "\n".join(lines))

        except Exception as e:
            logging.warning(f"[players] {server['name']} — ошибка: {e}")
            messages.append(f"❌ {server['name']} — ошибка: {e}")

    await update.message.reply_text("\n\n".join(messages), parse_mode="Markdown")

# 📦 Экспорт хендлера
players_handler = CommandHandler("players", players)
