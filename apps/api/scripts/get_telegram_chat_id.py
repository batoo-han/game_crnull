"""
Скрипт для получения правильного Telegram chat_id.

Этот скрипт помогает получить правильный chat_id для настройки Telegram уведомлений.
В отличие от Taobao_Scraper, где chat_id берется из message.chat.id автоматически,
в нашем проекте нужно указать chat_id получателя явно.
"""

import os
import sys
from pathlib import Path

# Устанавливаем UTF-8 для вывода в Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import httpx
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

if not BOT_TOKEN or BOT_TOKEN == "CHANGE_ME":
    print("[ERROR] Ошибка: TELEGRAM_BOT_TOKEN не настроен в .env")
    print("   Укажите токен бота в .env: TELEGRAM_BOT_TOKEN=your_token_here")
    sys.exit(1)

print("=" * 60)
print("Получение Telegram chat_id")
print("=" * 60)
print(f"Токен бота: {BOT_TOKEN[:20]}...")
print()

# Метод 1: Получить обновления (getUpdates)
print("Метод 1: Получение обновлений через getUpdates")
print("-" * 60)
print("Инструкция:")
print("1. Найдите вашего бота в Telegram")
print("2. Отправьте боту любое сообщение (например, /start)")
print("3. Нажмите Enter для получения обновлений...")
input()

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
try:
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                updates = data.get("result", [])
                if updates:
                    print(f"\n[OK] Найдено {len(updates)} обновлений:\n")
                    for i, update in enumerate(updates, 1):
                        message = update.get("message", {})
                        chat = message.get("chat", {})
                        chat_id = chat.get("id")
                        chat_type = chat.get("type")
                        chat_title = chat.get("title", chat.get("first_name", "N/A"))
                        
                        print(f"Обновление {i}:")
                        print(f"  Chat ID: {chat_id}")
                        print(f"  Тип: {chat_type}")
                        print(f"  Название: {chat_title}")
                        if chat_type == "private":
                            print(f"  [USER] Это ваш user_id для личных сообщений!")
                        elif chat_type == "group":
                            print(f"  [GROUP] Это ID группы!")
                        elif chat_type == "channel":
                            print(f"  [CHANNEL] Это ID канала!")
                        print()
                else:
                    print("[ERROR] Нет обновлений. Отправьте боту сообщение и попробуйте снова.")
            else:
                print(f"[ERROR] Ошибка API: {data.get('description', 'Неизвестная ошибка')}")
        else:
            print(f"[ERROR] HTTP ошибка: {resp.status_code}")
            print(f"Ответ: {resp.text}")
except Exception as e:
    print(f"[ERROR] Ошибка: {e}")

print()
print("=" * 60)
print("Метод 2: Получение информации о боте (getMe)")
print("-" * 60)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
try:
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                bot_id = bot_info.get("id")
                bot_username = bot_info.get("username", "N/A")
                bot_first_name = bot_info.get("first_name", "N/A")
                
                print(f"\n[OK] Информация о боте:")
                print(f"  Bot ID: {bot_id}")
                print(f"  Username: @{bot_username}")
                print(f"  Имя: {bot_first_name}")
                print()
                print(f"[WARNING] ВАЖНО: Bot ID ({bot_id}) НЕ подходит для TELEGRAM_CHAT_ID!")
                print(f"   Боты не могут отправлять сообщения другим ботам.")
                print(f"   Используйте user_id (из метода 1) или ID канала/группы.")
            else:
                print(f"[ERROR] Ошибка API: {data.get('description', 'Неизвестная ошибка')}")
        else:
            print(f"[ERROR] HTTP ошибка: {resp.status_code}")
            print(f"Ответ: {resp.text}")
except Exception as e:
    print(f"[ERROR] Ошибка: {e}")

print()
print("=" * 60)
print("Рекомендации:")
print("=" * 60)
print("1. Для личных сообщений:")
print("   - Используйте ваш user_id из метода 1 (тип: private)")
print("   - Или напишите боту @userinfobot для получения вашего user_id")
print()
print("2. Для канала:")
print("   - Добавьте бота в канал как администратора")
print("   - Отправьте сообщение в канал")
print("   - Используйте метод 1 для получения ID канала (начинается с -100)")
print()
print("3. Для группы:")
print("   - Добавьте бота в группу")
print("   - Отправьте сообщение в группу")
print("   - Используйте метод 1 для получения ID группы (отрицательное число)")
print()
print("4. После получения правильного chat_id:")
print("   - Обновите .env: TELEGRAM_CHAT_ID=\"ваш_chat_id\"")
print("   - Или укажите в настройках админки")
print()

