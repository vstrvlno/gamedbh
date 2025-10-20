import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

from story import story  # импорт истории

# === Загрузка переменных окружения ===
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise ValueError("❌ Переменная BOT_TOKEN не найдена. Укажи её в Render → Environment.")

# === Настройка бота ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# === Хранилище прогресса пользователей ===
user_progress = {}  # {user_id: scene_name}


# === Функция создания клавиатуры выбора ===
def create_choice_keyboard(choices, include_nav=False):
    keyboard = InlineKeyboardMarkup()
    for choice in choices:
        keyboard.add(InlineKeyboardButton(choice["text"], callback_data=choice["next"]))
    if include_nav:
        keyboard.row(
            InlineKeyboardButton("🔄 Начать заново", callback_data="intro"),
            InlineKeyboardButton("📜 Моя глава", callback_data="current"),
        )
    return keyboard


# === Отправка сцены пользователю ===
async def send_scene(message_or_callback, user_id, scene_name):
    scene = story.get(scene_name)
    if not scene:
        await message_or_callback.answer("История закончилась 🌌")
        return

    user_progress[user_id] = scene_name

    text = f"<b>{scene['title']}</b>\n\n{scene['text']}"
    keyboard = create_choice_keyboard(scene.get("choices", []), include_nav=True)

    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, reply_markup=keyboard)


# === Команда /start ===
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    await message.answer("👋 Добро пожаловать в текстовую игру!\nВыбери свой путь.")
    await send_scene(message, user_id, "intro")


# === Команда /admin (проверка админских прав) ===
@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("🔐 Админ-панель активна. Всё работает корректно.")
    else:
        await message.answer("⛔ У вас нет доступа к админ-панели.")


# === Обработка кнопок ===
@dp.callback_query()
async def handle_choice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if data == "current":
        current = user_progress.get(user_id, "intro")
        await send_scene(callback, user_id, current)
        return

    await send_scene(callback, user_id, data)


# === HTTP endpoint для Render (чтобы контейнер не падал) ===
async def healthcheck(request):
    return web.Response(text="Bot is running!")

def setup_webhook():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    return app


# === Основной запуск ===
async def main():
    logging.basicConfig(level=logging.INFO)
    print("✅ Бот запущен на Render и готов к работе")

    app = setup_webhook()

    # Параллельно запускаем aiohttp-сервер и бота
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
