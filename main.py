import os
from dotenv import load_dotenv

import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import BotCommand
from aiogram.types.input_file import InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from data_shape import get_data, search_city
from db_conn import update_user, get_user_data

load_dotenv()

ADMIN = os.getenv('ADMIN')
TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

commands = [
    BotCommand(command='/start', description='Начало работы с ботом'),
    BotCommand(command='/setcity', description='Сменить установленный город'),
    BotCommand(command='/help', description='Вывести все доступные команды'),
]


class User(StatesGroup):
    city = State()


class TimeTask(StatesGroup):
    time_task = State()


# Функция формирования и отправки сообщения с информацией
async def send_news(user_id):
    data = get_data(user_id)
    
    forecasts_text = ''
    if data['forecasts']:
        for i in data['forecasts']:
            forecasts_text += f"{i['date']}: ☀{i['day']}°C - 🌒 {i['night']}°C\n\n\n"

    text = f"Температура: <b>{data['temp_fact']}°C</b>, ощущается <b>{data['feels_like']}°C</b>\n" \
           f"{data['condition_fact']}\n\n" \
           f"{forecasts_text}" \
           f"Доллар: <b>{data['usd']}</b>{data['usd_changes']}\nЕвро: <b>{data['eur']}</b>{data['eur_changes']}\n\n" \
           f"Время: <b>{data['time']}</b> <i>{data['date']}</i>"
    photo = InputFile(f"weather_images/{data['photo']}.jpg")

    await bot.send_photo(user_id, photo=photo, caption=text, parse_mode='HTML')


@dp.message_handler(commands=['help'])
async def send_help(message):
    user_id = message.from_user.id
    db_user = get_user_data(user_id)

    if db_user:
        city_info = f"Ваш город: <b>{db_user['city']}</b>\n" \
                    f"Часовой пояс: <b>{db_user['timezone']}</b>\n"
    else:
        city_info = ''

    await message.answer('Данный бот будет отправлять тебе данные прогноза погоды и курса валют.\n\n'
                         'Для получения сообщения по времени введи /task, либо отправь любое сообщение.\n\n'
                         f'{city_info}\n'
                         'Доступные команды:\n'
                         '/task - прогноз по расписанию,\n'
                         '/start - начало работы,\n'
                         '/setcity - сменить город,\n'
                         '/help - помощь.',
                         parse_mode='HTML')


@dp.message_handler(commands=['start'])
async def send_start(message):
    user_id = message.from_user.id
    db_data = get_user_data(user_id)

    if db_data:
        text = f"Ваш город: <b>{db_data['city']}</b>\n" \
               f"Часовой пояс: <b>{db_data['timezone']}</b>\n\n" \
               f"<i>Для смены города введите</i> /setcity"

        await message.answer(text, parse_mode='HTML')
    else:
        await message.answer('Напиши свой город:')
        await User.city.set()


@dp.message_handler(state=User.city)
async def city_chosen(message: types.Message, state: FSMContext):
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

        update_user(
            tg_id=message.from_user.id,
            city=obj['city'],
            timezone=obj['timezone'],
            lat=obj['lat'],
            lon=obj['lon']
        )
        await message.answer(text, parse_mode='HTML')
    else:
        await message.answer(f"Такого города нет, попробуйте еще раз: /setcity или /start")


@dp.message_handler(commands=['setcity'])
async def send_setcity(message):
    user_id = message.from_user.id
    db_user = get_user_data(user_id)

    if db_user:
        text = f"Ваш город: <b>{db_user['city']}</b>\n" \
               f"Часовой пояс: <b>{db_user['timezone']}</b>\n\n" \
               f"Введите название нового города:"
        await message.answer(text, parse_mode='HTML')
        await User.city.set()
    else:
        await send_start(message)


@dp.message_handler()
async def send_answer(message):
    db_user = get_user_data(message.from_user.id)
    if db_user:
        await send_news(message.from_user.id)
    else:
        await message.answer('Вы не зарегистрированы, введите команду /start')


async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    await bot.set_my_commands(commands)

    # For scheduled mailing
    # aioschedule.every().day.at('7:00').do(send_news, ADMIN)
    # asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(
        dispatcher=dp,
        on_startup=on_startup,
    )
