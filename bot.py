# bot.py — исправленная версия для работы с story.py (500 узлов)
import os
import logging
import asyncio
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импорт сгенерированного story (500 узлов)
from story import story

# ---- Настройки ----
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в переменных окружения")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Структура состояний игроков: players[user_id] = {"current": int, "status": "playing"/"lost"/"finished"}
players: dict[int, dict] = {}

# ---- Хэндлеры ----
@dp.message(Command("start"))
async def start_game(message: types.Message):
    user_id = message.from_user.id
    # инициализируем нового игрока
    players[user_id] = {"current": 1, "status": "playing"}
    await send_story(message, user_id)


async def send_story(message: types.Message, user_id: int):
    """
    Отправляет пользователю текущую сцену.
    message: message object (используется для reply)
    """
    state = players.get(user_id)
    if not state:
        await message.answer("Ошибка состояния — запустите /start")
        return

    if state.get("status") != "playing":
        # игра окончена
        return

    current = state["current"]
    event = story.get(current)
    if not event:
        await message.answer("История закончилась.")
        state["status"] = "finished"
        return

    # Терминальный узел — нет choices или есть поле result
    if "choices" not in event or event.get("result") is not None:
        result = event.get("result", "lose")
        explanation = event.get("explanation", "Причина не указана.")
        title = event.get("text", "")
        if result == "win":
            await message.answer(f"✅ Победа!\n\n{title}\n\nПочему: {explanation}")
            state["status"] = "finished"
        else:
            await message.answer(f"❌ Поражение.\n\n{title}\n\nПочему: {explanation}")
            state["status"] = "lost"
        return

    # Обычная сцена с выбором
    text = event["text"]
    keyboard = InlineKeyboardMarkup()
    for key, choice in event.get("choices", {}).items():
        keyboard.add(InlineKeyboardButton(text=choice["text"][:50], callback_data=key))

    await message.answer(text, reply_markup=keyboard)


@dp.callback_query()
async def handle_choice(callback: types.CallbackQuery):
    """
    Обрабатываем нажатие кнопки. callback.data имеет формат "{node}|{choice_key}".
    """
    user_id = callback.from_user.id

    if user_id not in players or players[user_id].get("status") != "playing":
        await callback.answer("Игра неактивна. Наберите /start", show_alert=False)
        return

    data = callback.data or ""
    parts = data.split("|")
    if len(parts) != 2:
        await callback.answer("Неверный формат выбора.", show_alert=False)
        return

    try:
        node = int(parts[0])
    except ValueError:
        await callback.answer("Неверный узел.", show_alert=False)
        return

    choice_key = parts[1]

    
    # 💾 Сохраняем выбранную роль, если она есть
    if "role" in choice:
        players[user_id]["role"] = choice["role"]

    
    event = story.get(node)
    if not event or "choices" not in event:
        await callback.answer("Этот выбор уже неактуален.", show_alert=False)
        return

    if choice_key not in event["choices"]:
        await callback.answer("Недопустимый выбор.", show_alert=False)
        return

    # Получаем следующий узел по выбору (мы опираемся на узел, привязанный к кнопке)
    next_event = event["choices"][choice_key]["next"]

    # Логируем выбор
    logger.info("User %s chose %s at node %s -> next %s", user_id, choice_key, node, next_event)

    # Обновляем состояние игрока на следующий узел
    players[user_id]["current"] = next_event

    # Обновляем текст предыдущего сообщения, показывая совершённый выбор
    try:
        await callback.message.edit_text(f"Вы выбрали: {event['choices'][choice_key]['text']}")
    except Exception as e:
        logger.debug("Не удалось отредактировать сообщение: %s", e)

    await callback.answer()  # убирает спиннер у кнопки

    # Отправляем следующую сцену (используем callback.message как контекст для ответов)
    await send_story(callback.message, user_id)


# ---- Web health endpoint + запуск polling ----
async def handle_http(request):
    return web.Response(text="Bot is running")

async def main():
    # HTTP app
    app = web.Application()
    app.router.add_get("/", handle_http)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("HTTP server started on port %s", port)

    # Запускаем polling в таске
    bot_task = asyncio.create_task(dp.start_polling(bot))
    try:
        await bot_task
    finally:
        # корректный shutdown
        logger.info("Stopping HTTP runner")
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
