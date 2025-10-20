import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from story import story  # ✅ импорт твоего story.py

# ----------------------------
# 🔧 Настройки
# ----------------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Переменная окружения BOT_TOKEN не найдена!")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Состояние игроков
players = {}

# ----------------------------
# 🎮 Основная логика игры
# ----------------------------
@dp.message(Command("start"))
async def start_game(message: types.Message):
    """Начало игры"""
    user_id = message.from_user.id
    players[user_id] = {"current": 1, "status": "playing"}

    intro_text = (
        "🌆 Добро пожаловать в <b>Разрушенный Город</b>.\n\n"
        "Перед тобой — мир после катастрофы. Твоя цель — добыть вакцину и выжить.\n\n"
        "Сначала выбери, кто ты:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Учёный", callback_data="role_scientist")],
        [InlineKeyboardButton(text="⚔️ Солдат", callback_data="role_soldier")],
        [InlineKeyboardButton(text="💉 Медик", callback_data="role_medic")],
        [InlineKeyboardButton(text="🕵️ Разведчик", callback_data="role_scout")]
    ])
    await message.answer(intro_text, reply_markup=keyboard)


@dp.callback_query()
async def handle_choice(callback: types.CallbackQuery):
    """Обработка всех выборов"""
    user_id = callback.from_user.id

    # Если игрок ещё не выбрал роль
    if callback.data.startswith("role_"):
        role = callback.data.split("_")[1]
        players[user_id] = {
            "current": 1,
            "status": "playing",
            "role": role
        }
        await callback.message.answer(
            f"Вы выбрали роль: <b>{role.capitalize()}</b>.\n\n"
            "История начинается..."
        )
        await send_story(callback.message, user_id)
        await callback.answer()
        return

    # Проверяем, активна ли игра
    if user_id not in players or players[user_id]["status"] != "playing":
        await callback.answer("Игра неактивна. Напиши /start чтобы начать заново.")
        return

    current_state = players[user_id]["current"]
    event = story.get(current_state)

    if not event:
        await callback.message.answer("⚠️ Ошибка сюжета. История обрывается.")
        players[user_id]["status"] = "finished"
        await callback.answer()
        return

    # Обработка выбора
    choice_key = callback.data
    if choice_key not in event.get("choices", {}):
        await callback.answer("❌ Недопустимый выбор.")
        return

    next_step = event["choices"][choice_key]["next"]
    players[user_id]["current"] = next_step

    # Проверка завершения
    if next_step == 0:
        await callback.message.answer("💀 Вы проиграли. История окончена.")
        players[user_id]["status"] = "lost"
        await callback.answer()
        return

    if next_step == -1:
        await callback.message.answer("🏆 Поздравляем! Вы успешно завершили историю!")
        players[user_id]["status"] = "finished"
        await callback.answer()
        return

    # Иначе продолжаем историю
    await send_story(callback.message, user_id)
    await callback.answer()


async def send_story(message: types.Message, user_id: int):
    """Отправка сцены"""
    state = players[user_id]
    current = state["current"]

    if current not in story:
        await message.answer("История завершилась.")
        state["status"] = "finished"
        return

    event = story[current]
    text = f"📖 <b>Сцена {current}</b>\n\n{event['text']}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for key, choice in event.get("choices", {}).items():
        btn_text = choice["text"]
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=key)])

    await message.answer(text, reply_markup=keyboard)


# ----------------------------
# 🌐 Webhook или Polling (Render-friendly)
# ----------------------------
async def main():
    logging.basicConfig(level=logging.INFO)
    print("✅ Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
