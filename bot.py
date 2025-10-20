import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from story import story  # импорт твоей истории

# -----------------------------------------------------
# 🔧 Настройки
# -----------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в переменных окружения!")

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Состояние игроков
players = {}

# -----------------------------------------------------
# 🎮 Функции
# -----------------------------------------------------
async def send_story(message_or_callback, user_id: int):
    """Отправка текущей сцены пользователю"""
    state = players.get(user_id)
    if not state:
        return

    current = state["current"]
    status = state["status"]

    # Проигрыш
    if current == 0:
        text = "💀 Вы проиграли.\n\nПричина: " + state.get("reason", "неизвестная ошибка.")
        await message_or_callback.answer(text)
        state["status"] = "lost"
        return

    # Победа
    if current == -1:
        await message_or_callback.answer("🏆 Победа! История завершена успешно.")
        state["status"] = "finished"
        return

    event = story.get(current)
    if not event:
        await message_or_callback.answer("⚠️ История закончилась или повреждена.")
        state["status"] = "finished"
        return

    text = f"<b>{event['text']}</b>"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Добавляем кнопки
    for key, choice in event.get("choices", {}).items():
        btn_text = f"{key.upper()}: {choice['text']}"
        button = InlineKeyboardButton(text=btn_text, callback_data=key)
        keyboard.inline_keyboard.append([button])

    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=keyboard)
    else:
        await message_or_callback.message.edit_text(text, reply_markup=keyboard)


# -----------------------------------------------------
# 🚀 Команда /start
# -----------------------------------------------------
@dp.message(Command("start"))
async def start_game(message: types.Message):
    user_id = message.from_user.id
    players[user_id] = {"current": 1, "status": "playing"}
    await message.answer("👋 Добро пожаловать в игру!\n\nВы начинаете путь выжившего в разрушенном городе.")
    await send_story(message, user_id)


# -----------------------------------------------------
# ⚙️ Обработка выбора игрока
# -----------------------------------------------------
@dp.callback_query(F.data)
async def handle_choice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    state = players.get(user_id)

    if not state or state["status"] != "playing":
        await callback.answer("Игра неактивна. Введите /start.")
        return

    current = state["current"]
    event = story.get(current)
    if not event:
        await callback.answer("История не найдена.")
        return

    data = callback.data.lower()
    if data not in event["choices"]:
        await callback.answer("Неверный выбор.")
        return

    next_step = event["choices"][data]["next"]
    reason = event["choices"][data].get("reason")

    if next_step == 0:
        state["reason"] = reason or "Вы приняли неверное решение."
    state["current"] = next_step

    await send_story(callback, user_id)
    await callback.answer()


# -----------------------------------------------------
# ▶️ Точка входа
# -----------------------------------------------------
async def main():
    logging.info("✅ Бот запущен и слушает Telegram.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("⛔ Бот остановлен вручную.")
