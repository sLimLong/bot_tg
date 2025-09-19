#!/bin/bash

echo "🔧 Проверка Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 не найден."
    exit 1
fi

echo "📦 Создание виртуального окружения..."
if [ ! -d "venv311" ]; then
    python3.11 -m venv venv311
fi

echo "🚀 Активация окружения..."
source venv311/bin/activate

echo "📦 Обновление pip..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "📦 Установка зависимостей..."
    pip install -r requirements.txt
else
    pip install python-telegram-bot[job-queue]==20.3 aiohttp requests
fi

echo "🚀 Запуск main.py и discord_forward.py..."

# Запуск двух ботов параллельно
python main.py &
PID1=$!

python discord_forward.py &
PID2=$!

echo "🧭 main.py PID=$PID1"
echo "🧭 discord_forward.py PID=$PID2"

# Ожидаем завершения обоих
wait $PID1
wait $PID2

echo "✅ Оба бота завершили работу"
