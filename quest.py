import time, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from config import SERVERS

QUESTS = [
    {
        "id": 1,
        "title": "Убей 10 зомби",
        "type": "kill",
        "target": 10,
        "reward": "💰 100 монет",
        "item_reward": {"item": "coin", "count": 100}
    },
    {
        "id": 2,
        "title": "Найди 3 банки кофе",
        "type": "collect",
        "item": "coffee",
        "target": 3,
        "reward": "☕ 1 супер-кофе",
        "item_reward": {"item": "supercoffee", "count": 1}
    }
]

user_quests = {}  # user_id → {"id": quest_id, "progress": int}
quest_cooldowns = {}  # (user_id, quest_id) → timestamp
COOLDOWN_SECONDS = 72 * 3600

# 🎮 Главное меню
async def quest_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[InlineKeyboardButton("📋 Выбрать квест", callback_data="menu_select")]]
    user_id = update.effective_user.id
    if user_quests.get(user_id):
        buttons.append([InlineKeyboardButton("📌 Прогресс", callback_data="menu_progress")])
        buttons.append([InlineKeyboardButton("🏆 Завершить", callback_data="menu_complete")])
    buttons.append([InlineKeyboardButton("🆔 Установить EntityID", callback_data="menu_setid")])
    buttons.append([InlineKeyboardButton("🌐 Выбрать сервер", callback_data="menu_server")])
    await update.message.reply_text("🎮 Меню квестов:", reply_markup=InlineKeyboardMarkup(buttons))

# 📋 Список квестов
async def quest_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    keyboard = []
    for q in QUESTS:
        cooldown_key = (user_id, q["id"])
        last_completed = quest_cooldowns.get(cooldown_key, 0)
        active = user_quests.get(user_id, {}).get("id") == q["id"]
        status = "🟡 Активен" if active else "🔴 Кулдаун" if now - last_completed < COOLDOWN_SECONDS else "🟢 Доступен"
        button_text = f"{q['title']} ({status})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"quest_{q['id']}")])
    await update.callback_query.edit_message_text("📋 Ваши квесты:", reply_markup=InlineKeyboardMarkup(keyboard))

# 📌 Прогресс
async def quest_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    quest_data = user_quests.get(user_id)
    if not quest_data:
        await update.callback_query.edit_message_text("❌ У вас нет активного задания.")
        return
    quest = next((q for q in QUESTS if q["id"] == quest_data["id"]), None)
    await update.callback_query.edit_message_text(f"📌 Задание: {quest['title']}\nПрогресс: {quest_data['progress']}/{quest['target']}")

# 🏆 Завершение
async def quest_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    quest_data = user_quests.get(user_id)
    if not quest_data:
        await update.message.reply_text("❌ У вас нет активного задания.")
        return
    quest = next((q for q in QUESTS if q["id"] == quest_data["id"]), None)
    if quest_data["progress"] < quest["target"]:
        await update.message.reply_text(f"⏳ Задание ещё не выполнено.\nПрогресс: {quest_data['progress']}/{quest['target']}")
        return

    app_data = context.application.user_data.setdefault(user_id, {})
    server_index = app_data.get("selected_index")
    entity_id = app_data.get("entity_id")

    if server_index is None or not isinstance(server_index, int) or server_index >= len(SERVERS):
        await update.message.reply_text("❌ Сервер не выбран или недоступен.")
        return

    server = SERVERS[server_index]
    reward_text = quest.get("reward", "🎁 Награда")
    item_reward = quest.get("item_reward")

    if item_reward and entity_id:
        try:
            response = requests.post(
                f"{server['url']}/api/giveitem",
                auth=server['auth'],
                json={"entityid": entity_id, "item": item_reward["item"], "count": item_reward["count"]},
                timeout=5
            )
            if response.status_code == 200:
                await update.message.reply_text(
                    f"🏆 Задание выполнено!\nВы получили: {reward_text}\n📦 Выдано: {item_reward['item']} x{item_reward['count']}"
                )
            else:
                await update.message.reply_text(f"✅ Задание выполнено, но ошибка при выдаче:\n{response.text}")
        except Exception as e:
            await update.message.reply_text(f"✅ Задание выполнено, но ошибка при выдаче:\n{e}")
    else:
        await update.message.reply_text(f"🏆 Задание выполнено!\nВы получили: {reward_text}")

    quest_cooldowns[(user_id, quest["id"])] = time.time()
    del user_quests[user_id]

# 🆔 Установка EntityID
async def set_entity_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Использование: /setid <EntityID>")
        return
    entity_id = context.args[0]
    user_id = update.effective_user.id
    context.application.user_data.setdefault(user_id, {})["entity_id"] = entity_id
    await update.message.reply_text(f"✅ EntityID установлен: `{entity_id}`", parse_mode="Markdown")

# 🌐 Выбор сервера
async def handle_server_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace("server_", ""))
    user_id = update.effective_user.id
    context.application.user_data.setdefault(user_id, {})["selected_index"] = index
    await query.edit_message_text(f"✅ Сервер выбран: {SERVERS[index]['name']}")

# 🎯 Выбор квеста
async def handle_quest_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    quest_id = int(query.data.replace("quest_", ""))
    quest = next((q for q in QUESTS if q["id"] == quest_id), None)
    now = time.time()
    cooldown_key = (user_id, quest_id)
    last_completed = quest_cooldowns.get(cooldown_key, 0)
    if now - last_completed < COOLDOWN_SECONDS:
        remaining = int((COOLDOWN_SECONDS - (now - last_completed)) / 3600)
        await query.edit_message_text(f"⏳ Этот квест будет доступен через {remaining} ч.")
        return
    user_quests[user_id] = {"id": quest_id, "progress": 0}
    await query.edit_message_text(f"✅ Вы выбрали: {quest['title']}\nПрогресс: 0/{quest['target']}")

# 📲 Обработка меню
async def handle_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "menu_select":
        await quest_list(update, context)
    elif query.data == "menu_progress":
        await quest_progress(update, context)
    elif query.data == "menu_complete":
        await quest_complete(update, context)
    elif query.data == "menu_setid":
        await query.edit_message_text("🆔 Введите команду:\n`/setid <EntityID>`", parse_mode="Markdown")
    elif query.data == "menu_server":
        keyboard = [
            [InlineKeyboardButton(s["name"], callback_data=f"server_{i}")]
            for i, s in enumerate(SERVERS)
        ]
        await query.edit_message_text("🌐 Выберите сервер:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("❌ Неизвестное действие.")

# 📦 Экспорт хендлеров
quest_handlers = [
    CommandHandler("questmenu", quest_main_menu),
    CommandHandler("setid", set_entity_id),
    CommandHandler("complete", quest_complete),
    CallbackQueryHandler(handle_menu_action, pattern=r"^menu_"),
    CallbackQueryHandler(handle_server_choice, pattern=r"^server_"),
    CallbackQueryHandler(handle_quest_choice, pattern=r"^quest_")
]