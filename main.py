import os
import requests
from datetime import datetime
from dotenv import load_dotenv

import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import BotCommand
from aiogram.types.input_file import InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from web_server import keep_alive
from data_shape import get_data, search_city

load_dotenv()

ADMIN = os.getenv('ADMIN')
TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

DB_REPLIT = int(os.getenv('DB_REPLIT'))
'''
if DB_REPLIT:
    from replit import db
else:
    db = {}
'''
db = {}

commands = [
    BotCommand(command='/start', description='Начало работы с ботом'),
    BotCommand(command='/setcity', description='Сменить установленный город'),
    BotCommand(command='/help', description='Вывести все доступные комманды'),
    BotCommand(command='/print', description='test'),
]


class User(StatesGroup):
    city = State()


# Функция формирования и отправки сообщения с информацией
async def send_news_core(user_data):
    data = get_data(user_data)

    forecasts_text = ''
    for i in data['forecasts']:
        forecasts_text += f"{i['date']}: ☀{i['day']}°C - 🌒 {i['night']}°C\n"

    text = f"Тепература: {data['temp_fact']}°C, {data['condition_fact']}\n\n" \
           f"{forecasts_text}\n\n" \
           f"Доллар: {data['usd']}{data['usd_changes']}\nЕвро: {data['eur']}{data['eur_changes']}\n\n" \
           f"Время сервера: {data['time']} {data['date']} ({data['city']})"
    photo = InputFile(f"weather_images/{data['photo']}.jpg")

    await bot.send_photo(user_data['id'], photo=photo, caption=text)


async def send_news(user_id=None):
    if user_id:
        await send_news_core(db[user_id])
    else:
        for user in db:
            await send_news_core(db[user])


@dp.message_handler(commands=['help'])
async def send_help(message):
    user_id = message.from_user.id

    if user_id in db:
        city_info = f"Ваш город: <b>{db[user_id]['city']}</b>\n" \
                    f"Часовой пояс: <b>{db[user_id]['timezone']}</b>\n"
    else:
        city_info = ''

    await message.answer('Данный бот будет отправлять тебе данные прогноза погоды и курса валют.\n\n'
                         f'{city_info}'
                         'Доступные команды:\n'
                         '/start - начало работы,\n'
                         '/setcity - сменить город,\n'
                         '/help - помощь.', parse_mode='HTML')


@dp.message_handler(commands=['start'])
async def send_start(message):
    user_id = message.from_user.id

    if user_id in db:
        text = f"Ваш город: <b>{db[user_id]['city']}</b>\n" \
               f"Часовой пояс: <b>{db[user_id]['timezone']}</b>\n\n" \
               f"<i>Для смены города введите</i> /setcity"
        await message.answer(text, parse_mode='HTML')
    else:
        await message.answer('Напиши свой город:')
        await User.city.set()


@dp.message_handler(state=User.city)
async def city_choosen(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()
    await state.finish()

    obj = search_city(data['city'])
    if obj:
        if obj['region'] is None:
            region = ''
        else:
            region = ', ' + obj['region']

        text = f"Вы выбрали: <b>{obj['city']}{region}</b>\n\n" \
               f"<i>Для смены города введите</i> /setcity"
        await message.answer(text, parse_mode='HTML')

        db[message.from_user.id] = {
            'id': message.from_user.id,
            'city': obj['city'],
            'timezone': obj['timezone'],
            'lat': obj['lat'],
            'lon': obj['lon'],
        }
    else:
        await message.answer(f"Такого города нет, попробуйте еще раз: /start")


@dp.message_handler(commands=['setcity'])
async def send_cetcity(message):
    user_id = message.from_user.id

    if user_id in db:
        text = f"Ваш город: <b>{db[user_id]['city']}</b>\n" \
               f"Часовой пояс: <b>{db[user_id]['timezone']}</b>\n\n" \
               f"Введите название нового города:"
        await message.answer(text, parse_mode='HTML')
        await User.city.set()
    else:
        await send_start(message)


@dp.message_handler(commands=['print'])
async def send_print(message):
    await bot.send_message(message.from_user.id, str(db))


@dp.message_handler()
async def send_answer(message):
    if message.from_user.id in db:
        await send_news(message.from_user.id)
    else:
        await message.answer('Вас нет в базе. Введите комманду /start')


async def scheduler():
    aioschedule.every().day.at('2:30').do(send_news)
    aioschedule.every().day.at('7:00').do(send_news)
    aioschedule.every().day.at('11:00').do(send_news)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    await bot.set_my_commands(commands)

    keep_alive()
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
