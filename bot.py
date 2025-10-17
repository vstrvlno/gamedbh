# dbh_100_steps.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

players = {}

# Сценарий: шаг -> описание + выборы
# Для примера показаны первые 10 шагов; структуру легко расширять до 100
story = {
    1: {"text": "Вы — андроид-детектив. Сегодня начинается новое расследование.",
        "choices": {"a": {"text": "Идти на место преступления", "next": 2},
                    "b": {"text": "Игнорировать вызов", "next": 0},
                    "c": {"text": "Собрать информацию о подозреваемом", "next": 3}}},
    2: {"text": "На месте преступления вы видите следы крови и цифровой след.",
        "choices": {"a": {"text": "Следовать за кровью", "next": 4},
                    "b": {"text": "Проверить цифровой след", "next": 5},
                    "c": {"text": "Вызвать экспертов", "next": 6}}},
    3: {"text": "Вы изучаете досье. Подозреваемый был инженером в корпорации CyberLife.",
        "choices": {"a": {"text": "Посетить корпорацию", "next": 7},
                    "b": {"text": "Проверить его жильё", "next": 8},
                    "c": {"text": "Закрыть досье", "next": 0}}},
    4: {"text": "След приводит вас в подвал старого дома.",
        "choices": {"a": {"text": "Спуститься вниз", "next": 9},
                    "b": {"text": "Вызвать подкрепление", "next": 6},
                    "c": {"text": "Уйти", "next": 0}}},
    5: {"text": "Цифровой след ведёт в сеть подпольных андроидов.",
        "choices": {"a": {"text": "Взломать систему", "next": 10},
                    "b": {"text": "Отправить запрос в штаб", "next": 6},
                    "c": {"text": "Игнорировать", "next": 0}}},
    6: {"text": "Подкрепление прибыло. Вы обсуждаете план действий.",
        "choices": {"a": {"text": "Напасть на укрытие", "next": 11},
                    "b": {"text": "Попытаться переговорить", "next": 12},
                    "c": {"text": "Ждать приказа", "next": 13}}},
    7: {"text": "В офисе CyberLife вас встречает директор.",
        "choices": {"a": {"text": "Показать ордер", "next": 14},
                    "b": {"text": "Пойти без разрешения", "next": 0},
                    "c": {"text": "Собрать информацию незаметно", "next": 15}}},
    8: {"text": "В доме подозреваемого вы находите андроидов без сознания.",
        "choices": {"a": {"text": "Активировать одного", "next": 16},
                    "b": {"text": "Осмотреть дом", "next": 17},
                    "c": {"text": "Уйти", "next": 0}}},
    9: {"text": "Подвал пуст, но активен терминал.",
        "choices": {"a": {"text": "Подключиться", "next": 18},
                    "b": {"text": "Уничтожить терминал", "next": 0},
                    "c": {"text": "Отправить данные штабу", "next": 19}}},
    10: {"text": "Взлом удался. Вы получаете координаты базы андроидов.",
         "choices": {"a": {"text": "Идти туда", "next": 20},
                     "b": {"text": "Сообщить команде", "next": 6},
                     "c": {"text": "Удалить данные", "next": 0}}},

    # ---- Ходы 11–30 ----
    11: {"text": "Вы штурмуете укрытие. Внутри идёт бой.",
         "choices": {"a": {"text": "Продвигаться вперёд", "next": 21},
                     "b": {"text": "Отступить", "next": 0},
                     "c": {"text": "Искать обходной путь", "next": 22}}},
    12: {"text": "Вы пытаетесь убедить лидера андроидов сдаться.",
         "choices": {"a": {"text": "Использовать логику", "next": 23},
                     "b": {"text": "Проявить сочувствие", "next": 24},
                     "c": {"text": "Угрожать", "next": 0}}},
    13: {"text": "Пока вы ждёте, преступники успевают скрыться.",
         "choices": {"a": {"text": "Преследовать", "next": 25},
                     "b": {"text": "Остаться на месте", "next": 0},
                     "c": {"text": "Запросить дрона", "next": 26}}},
    14: {"text": "Директор соглашается на допрос.",
         "choices": {"a": {"text": "Задать вопросы о проектах", "next": 27},
                     "b": {"text": "Наблюдать за реакцией", "next": 28},
                     "c": {"text": "Уйти", "next": 0}}},
    15: {"text": "Вы находите скрытый сервер компании.",
         "choices": {"a": {"text": "Скопировать данные", "next": 29},
                     "b": {"text": "Взломать сервер", "next": 30},
                     "c": {"text": "Сообщить начальству", "next": 6}}},
    16: {"text": "Андроид просыпается и смотрит на вас.",
         "choices": {"a": {"text": "Задать вопрос", "next": 31},
                     "b": {"text": "Выключить его", "next": 0},
                     "c": {"text": "Освободить", "next": 32}}},
    17: {"text": "Вы находите улики, указывающие на сеть мятежников.",
         "choices": {"a": {"text": "Отправить отчёт", "next": 6},
                     "b": {"text": "Продолжить поиск", "next": 33},
                     "c": {"text": "Уничтожить улики", "next": 0}}},
    18: {"text": "Вы подключаетесь к терминалу — там вирус.",
         "choices": {"a": {"text": "Отключиться", "next": 0},
                     "b": {"text": "Изолировать вирус", "next": 34},
                     "c": {"text": "Сканировать глубже", "next": 35}}},
    19: {"text": "Штаб благодарит за данные. Новые координаты получены.",
         "choices": {"a": {"text": "Следовать туда", "next": 36},
                     "b": {"text": "Игнорировать", "next": 0},
                     "c": {"text": "Передать данные спецотряду", "next": 37}}},
    20: {"text": "Вы прибываете к базе андроидов в горах.",
         "choices": {"a": {"text": "Проникнуть тайно", "next": 38},
                     "b": {"text": "Зайти в открытую", "next": 0},
                     "c": {"text": "Подождать ночи", "next": 39}}},

    # ---- Промежуточные шаги (31–60) ----
    31: {"text": "Андроид рассказывает о заговоре внутри CyberLife.",
         "choices": {"a": {"text": "Записать всё", "next": 40},
                     "b": {"text": "Сообщить руководству", "next": 41},
                     "c": {"text": "Не верить ему", "next": 0}}},
    32: {"text": "Освобождённый андроид помогает вам найти укрытие.",
         "choices": {"a": {"text": "Следовать за ним", "next": 42},
                     "b": {"text": "Не доверять", "next": 0},
                     "c": {"text": "Сообщить напарнику", "next": 43}}},
    33: {"text": "Вы находите скрытую лабораторию.",
         "choices": {"a": {"text": "Войти", "next": 44},
                     "b": {"text": "Отправить координаты", "next": 37},
                     "c": {"text": "Взорвать лабораторию", "next": 0}}},
    34: {"text": "Вы успешно изолируете вирус и получаете доступ к логам.",
         "choices": {"a": {"text": "Изучить логи", "next": 45},
                     "b": {"text": "Удалить их", "next": 0},
                     "c": {"text": "Скопировать", "next": 46}}},
    35: {"text": "Вирус заражает вашу систему. Вы теряете контроль.",
         "choices": {"a": {"text": "Бороться", "next": 47},
                     "b": {"text": "Сдаться", "next": 0},
                     "c": {"text": "Отключить питание", "next": 48}}},
    36: {"text": "Вы прибываете на новую базу данных.",
         "choices": {"a": {"text": "Проникнуть внутрь", "next": 49},
                     "b": {"text": "Ждать команды", "next": 50},
                     "c": {"text": "Покинуть миссию", "next": 0}}},
    37: {"text": "Спецотряд действует по вашим данным. Вы наблюдаете издалека.",
         "choices": {"a": {"text": "Вмешаться", "next": 51},
                     "b": {"text": "Оставаться наблюдателем", "next": 52},
                     "c": {"text": "Помочь им тайно", "next": 53}}},
    38: {"text": "Вы крадётесь по периметру базы.",
         "choices": {"a": {"text": "Проникнуть внутрь", "next": 54},
                     "b": {"text": "Вернуться", "next": 0},
                     "c": {"text": "Вызвать дрон-разведчик", "next": 55}}},
    39: {"text": "Ночь наступает. Охрана ослабла.",
         "choices": {"a": {"text": "Проникнуть", "next": 54},
                     "b": {"text": "Ожидать рассвета", "next": 0},
                     "c": {"text": "Устроить засаду", "next": 56}}},

    # ---- Средние ходы (61–90) ----
    61: {"text": "Вы приближаетесь к финалу расследования.",
         "choices": {"a": {"text": "Объединить все улики", "next": 91},
                     "b": {"text": "Проверить напарника", "next": 62},
                     "c": {"text": "Пойти в одиночку", "next": 0}}},
    62: {"text": "Напарник ведёт себя странно. Возможно, он предатель.",
         "choices": {"a": {"text": "Следить за ним", "next": 63},
                     "b": {"text": "Довериться ему", "next": 0},
                     "c": {"text": "Сообщить в штаб", "next": 64}}},
    63: {"text": "Вы следите и узнаёте: напарник связан с CyberLife.",
         "choices": {"a": {"text": "Арестовать", "next": 65},
                     "b": {"text": "Дать шанс объясниться", "next": 66},
                     "c": {"text": "Отступить", "next": 0}}},
    64: {"text": "Штаб требует доказательства.",
         "choices": {"a": {"text": "Собрать улики", "next": 67},
                     "b": {"text": "Подделать отчёт", "next": 0},
                     "c": {"text": "Отложить расследование", "next": 68}}},
    65: {"text": "Вы арестовали напарника. Он предупреждает о ловушке.",
         "choices": {"a": {"text": "Освободить", "next": 69},
                     "b": {"text": "Игнорировать", "next": 70},
                     "c": {"text": "Проверить ловушку", "next": 71}}},
    66: {"text": "Напарник признаётся, что хотел вас защитить.",
         "choices": {"a": {"text": "Простить", "next": 72},
                     "b": {"text": "Не верить", "next": 0},
                     "c": {"text": "Сообщить командованию", "next": 73}}},

    # ---- Финальные ходы (91–100) ----
    91: {"text": "Все улики собраны. Осталось раскрыть заговор.",
         "choices": {"a": {"text": "Пойти в штаб CyberLife", "next": 94},
                     "b": {"text": "Вызвать прессу", "next": 95},
                     "c": {"text": "Уничтожить улики", "next": 0}}},
    94: {"text": "Вы проникаете в центральный офис CyberLife.",
         "choices": {"a": {"text": "Взломать главный сервер", "next": 97},
                     "b": {"text": "Попытаться уговорить директора", "next": 98},
                     "c": {"text": "Отступить", "next": 0}}},
    95: {"text": "Пресса поднимает шум. CyberLife теряет влияние.",
         "choices": {"a": {"text": "Принять награду и уйти", "next": -1},
                     "b": {"text": "Продолжить борьбу", "next": 99}}},
    97: {"text": "Вы получаете доказательства, что компания контролирует андроидов.",
         "choices": {"a": {"text": "Опубликовать данные", "next": 99},
                     "b": {"text": "Скрыть правду", "next": 0}}},
    98: {"text": "Директор предлагает сделку.",
         "choices": {"a": {"text": "Согласиться", "next": 0},
                     "b": {"text": "Отказать", "next": 99}}},
    99: {"text": "Истина раскрыта. Люди и андроиды получают шанс на мир.",
         "choices": {"a": {"text": "Завершить историю", "next": -1}}}
}



@dp.message(Command("start"))
async def start_game(message: types.Message):
    user_id = message.from_user.id
    players[user_id] = {"current": 1, "status": "playing"}
    await send_story(message, user_id)

async def send_story(message, user_id):
    state = players[user_id]
    current = state["current"]

    if state["status"] != "playing":
        return
    
    if current == 0:
        await message.answer("Вы проиграли. Конец истории.")
        state["status"] = "lost"
        return
    if current == -1:
        await message.answer("Поздравляем! История завершена успешно!")
        state["status"] = "finished"
        return

    event = story.get(current)
    if not event:
        await message.answer("История закончилась.")
        state["status"] = "finished"
        return

    text = event["text"]
    keyboard = InlineKeyboardMarkup()
    for key, choice in event.get("choices", {}).items():
        keyboard.add(InlineKeyboardButton(text=choice["text"], callback_data=key))

    await message.answer(text, reply_markup=keyboard)

@dp.callback_query()
async def handle_choice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in players or players[user_id]["status"] != "playing":
        await callback.answer("Игра неактивна. Наберите /start")
        return

    state = players[user_id]
    current = state["current"]
    choice_key = callback.data
    event = story.get(current)

    if choice_key not in event.get("choices", {}):
        await callback.answer("Недопустимый выбор.")
        return

    next_event = event["choices"][choice_key]["next"]
    state["current"] = next_event
    await callback.message.edit_text(f"Вы выбрали: {event['choices'][choice_key]['text']}")
    await send_story(callback.message, user_id)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(dp.start_polling(bot))
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
    asyncio.run(dp.start_polling(bot))
