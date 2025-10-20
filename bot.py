import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

from story import story  # словарь сцен: { "intro": {"title": "...", "text": "...", "choices":[{"text":"...", "next":"..."}]} }

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден. Добавь его в Render → Environment.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# хранение прогресса пользователей
user_progress: dict[int, str] = {}

def create_choice_keyboard(choices, include_nav=False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for choice in choices:
        # callback_data должен быть строкой и не длиннее 64 символов
        kb.add(InlineKeyboardButton(choice["text"], callback_data=str(choice["next"])))
    if include_nav:
        kb.row(
            InlineKeyboardButton("🔄 Начать заново", callback_data="intro"),
            InlineKeyboardButton("📜 Моя глава", callback_data="current"),
        )
    return kb

async def send_scene(event, user_id: int, scene_name: str):
    scene = story.get(scene_name)
    logger.info("Send scene %s to user %s: %s", scene_name, user_id, bool(scene))

    if not scene:
        # для callback используем answer, для сообщений — reply
        if isinstance(event, types.CallbackQuery):
            await event.answer("История закончилась 🌌")
        else:
            await event.answer("История закончилась 🌌")
        return

    user_progress[user_id] = scene_name

    text = f"<b>{scene.get('title','')}</b>\n\n{scene.get('text','')}"
    keyboard = create_choice_keyboard(scene.get("choices", []), include_nav=True)

    # если это callback — редактируем сообщение, иначе отправляем новое сообщение
    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=keyboard)
        except Exception as e:
            # если редактирование не удалось (например, сообщение удалено), отправляем новое
            logger.warning("Edit failed, sending new message: %s", e)
            await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
        await event.answer()
    else:
        # event — Message
        await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    await message.answer("👋 Добро пожаловать в текстовую игру!\nВыбери свой путь.")
    await send_scene(message, user_id, "intro")

@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("🔐 Админ-панель активна. Всё работает корректно.")
    else:
        await message.answer("⛔ У вас нет доступа к админ-панели.")

@dp.callback_query(F.data)
async def handle_choice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data
    logger.info("Callback from %s: %s", user_id, data)

    if data == "current":
        current = user_progress.get(user_id, "intro")
        await send_scene(callback, user_id, current)
        return

    # если ключа нет в истории — сообщаем пользователю
    if data not in story and data != "intro" and data != "current":
        await callback.answer("Неверный выбор или сцена не найдена.", show_alert=True)
        return

    await send_scene(callback, user_id, data)

# HTTP healthcheck для Render
async def healthcheck(request):
    return web.Response(text="Bot is running!")

def setup_webhook():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    return app

async def main():
    logger.info("✅ Бот запущен и готов к работе")
    app = setup_webhook()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
