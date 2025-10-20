import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
import asyncio

from story import story

# --- Настройки ---
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден. Добавь его в переменные окружения Render!")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# --- Игровое состояние пользователей ---
user_states = {}

# --- Клавиатура выбора ---
def make_keyboard(options):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for opt in options:
        kb.add(KeyboardButton(opt))
    return kb


# --- Команда /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = start_story()

    scene = user_states[user_id]
    await message.answer(scene["text"], reply_markup=make_keyboard(scene["choices"]))


# --- Обработка ответов ---
@dp.message()
async def handle_choice(message: types.Message):
    user_id = message.from_user.id
    user_input = message.text.strip()

    if user_id not in user_states:
        await message.answer("Введите /start, чтобы начать заново.")
        return

    current_scene = user_states[user_id]
    next_scene = get_next_scene(current_scene, user_input)

    if not next_scene:
        await message.answer("Некорректный выбор. Попробуй ещё раз.", 
                             reply_markup=make_keyboard(current_scene["choices"]))
        return

    user_states[user_id] = next_scene
    text = next_scene["text"]

    # Проверка конца сюжета
    if is_story_end(next_scene):
        await message.answer(text + "\n\n<b>Конец истории.</b>")
        user_states.pop(user_id, None)
    else:
        await message.answer(text, reply_markup=make_keyboard(next_scene["choices"]))


# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
