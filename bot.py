import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем историю
from story import story

# === Настройка окружения ===
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден. Добавь его в .env на Render")

# === Создаём бота (исправленный вариант для Aiogram 3.7+) ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# === Глобальное хранилище прогресса ===
user_progress = {}  # {user_id: scene_name}


# === Функция генерации клавиатуры ===
def create_choice_keyboard(choices):
    keyboard = InlineKeyboardMarkup()
    for choice in choices:
        keyboard.add(InlineKeyboardButton(choice["text"], callback_data=choice["next"]))
    return keyboard


# === Отправка сцены ===
async def send_scene(message_or_callback, user_id, scene_name):
    scene = story.get(scene_name)
    if not scene:
        await message_or_callback.answer("История закончена 🌌")
        return

    user_progress[user_id] = scene_name

    text = f"<b>{scene['title']}</b>\n\n{scene['text']}"
    keyboard = create_choice_keyboard(scene.get("choices", []))

    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, reply_markup=keyboard)


# === Команда /start ===
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await send_scene(message, message.from_user.id, "intro")


# === Обработка нажатий кнопок ===
@dp.callback_query()
async def handle_choice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    next_scene = callback.data
    await send_scene(callback, user_id, next_scene)


# === Основной запуск ===
async def main():
    logging.basicConfig(level=logging.INFO)
    print("✅ Бот запущен и готов к работе")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
