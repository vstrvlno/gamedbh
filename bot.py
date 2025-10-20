import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from story import chapter1, chapter2, chapter3, chapter4, chapter5

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Храним состояние игроков
players = {}

# -------------------------------
# Кнопки выбора ролей
# -------------------------------
def role_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧬 Учёный", callback_data="role_Учёный")],
        [InlineKeyboardButton(text="🪖 Солдат", callback_data="role_Солдат")],
        [InlineKeyboardButton(text="🧍 Выживший", callback_data="role_Выживший")]
    ])
    return kb


# -------------------------------
# Отправка следующего шага
# -------------------------------
async def send_step(chat_id, player, step_func):
    text, options = step_func(player)
    buttons = [[InlineKeyboardButton(text=o["text"], callback_data=o["goto"])] for o in options]
    await bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# -------------------------------
# /start
# -------------------------------
@dp.message()
async def cmd_start(message: types.Message):
    players[message.from_user.id] = {"step": 0, "role": None}
    await message.answer(
        "🌆 Добро пожаловать в разрушенный город.\n\n"
        "Ты стоишь среди пепла и руин. Но у тебя есть шанс изменить всё.\n"
        "Выбери, кем ты будешь:",
        reply_markup=role_keyboard()
    )


# -------------------------------
# Обработка выбора роли
# -------------------------------
@dp.callback_query(lambda c: c.data.startswith("role_"))
async def choose_role(callback: types.CallbackQuery):
    role = callback.data.split("_")[1]
    player = players.get(callback.from_user.id, {"step": 0})
    player["role"] = role
    player["step"] = 1
    players[callback.from_user.id] = player
    await callback.message.edit_text(f"Ты выбрал роль: *{role}*.\n\nИстория начинается...", parse_mode="Markdown")
    await asyncio.sleep(1)
    await send_step(callback.message.chat.id, player, chapter1.play)


# -------------------------------
# Универсальный обработчик шагов
# -------------------------------
@dp.callback_query(lambda c: c.data.startswith("goto_"))
async def handle_step(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = players.get(user_id)

    if not player:
        await callback.message.answer("Ошибка состояния. Начни с /start.")
        return

    step = callback.data.split("_")[1]

    if step == "ch2":
        await send_step(callback.message.chat.id, player, chapter2.play)
    elif step == "ch3":
        await send_step(callback.message.chat.id, player, chapter3.play)
    elif step == "ch4":
        await send_step(callback.message.chat.id, player, chapter4.play)
    elif step == "ch5":
        chapter5.play_chapter5(player)
    elif step == "end":
        await callback.message.edit_text("История закончилась. Используй /start чтобы начать заново.")
    else:
        await callback.message.answer("Неверный переход.")


# -------------------------------
# Запуск
# -------------------------------
async def main():
    print("✅ Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
