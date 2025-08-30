import requests
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from config import SERVERS, ALLOWED_ADMINS

async def show_player_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ALLOWED_ADMINS:
        await update.message.reply_text("🚫 У вас нет доступа к этой команде.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Использование: /apl <EntityID>")
        return

    entity_id = context.args[0]
    server = SERVERS[0]  # можно расширить на перебор всех серверов

    try:
        response = requests.get(
            f"{server['url']}/api/player",
            auth=server['auth'],
            timeout=5
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"⚠️ Ошибка при получении игроков:\nСтатус: {response.status_code}\nОтвет: {response.text}"
            )
            return

        data = response.json()
        players = data.get("data", {}).get("players", [])
        player = next((p for p in players if str(p.get("entityId")) == str(entity_id)), None)

        if not player:
            await update.message.reply_text(
                f"👻 Игрок с EntityID `{entity_id}` не найден.",
                parse_mode="Markdown"
            )
            return

        # Основные данные
        name = player.get("name", "Безымянный")
        pos = player.get("position", {})
        pos_text = f"X: {pos.get('x', '?')}, Y: {pos.get('y', '?')}, Z: {pos.get('z', '?')}"
        hp = player.get("health", "?")
        level = player.get("level", "?")
        online = "🟢 Онлайн" if player.get("online") else "🔴 Оффлайн"
        ping = player.get("ping", "?")
        kills = player.get("kills", {}).get("zombies", 0)

        # Статус бана
        ban_info = player.get("banned", {})
        ban_active = ban_info.get("banActive", False)
        ban_reason = ban_info.get("reason", "не указана")
        ban_until = ban_info.get("until", "не определено")
        ban_status = f"🚫 Забанен\nПричина: {ban_reason}\nДо: {ban_until}" if ban_active else "✅ Не забанен"

        # Steam-ссылка
        platform_data = player.get("platformId", {})
        steam_raw = platform_data.get("combinedString", "")
        steam_id = steam_raw.replace("Steam_", "") if steam_raw.startswith("Steam_") else None
        steam_link = f"[🔗 Steam профиль](https://findsteamid.com/steamid/{steam_id})" if steam_id else "❌ Steam ID не найден"

        # Ответ пользователю
        await update.message.reply_text(
            f"*🧍 Игрок:* {name}\n"
            f"*🆔 EntityID:* `{entity_id}`\n"
            f"*📶 Статус:* {online} (Ping: {ping})\n"
            f"*📈 Уровень:* {level}\n"
            f"*❤️ Здоровье:* {hp}\n"
            f"*📍 Позиция:* {pos_text}\n"
            f"*☠️ Убийства зомби:* {kills}\n"
            f"*🚨 Бан:* {ban_status}\n"
            f"{steam_link}",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при запросе:\n{e}")

# 📦 Экспорт хендлера
apl_handlers = [
    CommandHandler("apl", show_player_by_id)
]
