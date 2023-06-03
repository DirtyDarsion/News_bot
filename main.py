import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import BotCommand
from aiogram.types.input_file import InputFile
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
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
    # BotCommand(command='/task', description='Параметры рассылки по времени'),
    BotCommand(command='/start', description='Начало работы с ботом'),
    BotCommand(command='/setcity', description='Сменить установленный город'),
    BotCommand(command='/help', description='Вывести все доступные комманды'),
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
            forecasts_text += f"{i['date']}: ☀{i['day']}°C - 🌒 {i['night']}°C\n"
    else:
        forecasts_text = 'Ошибка в получении прогноза'

    text = f"Тепература: {data['temp_fact']}°C, {data['condition_fact']}\n\n" \
           f"{forecasts_text}\n\n" \
           f"Доллар: {data['usd']}{data['usd_changes']}\nЕвро: {data['eur']}{data['eur_changes']}\n\n" \
           f"Время: {data['time']} {data['date']}"
    photo = InputFile(f"weather_images/{data['photo']}.jpg")

    await bot.send_photo(user_id, photo=photo, caption=text)


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
                         '/task - прогноз по рассписанию,\n'
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
async def send_cetcity(message):
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

'''
Вызов прогноза по расписанию
Необходимо настроить под базу данных

@dp.message_handler(commands=['task'])
async def set_task(message):
    user_id = message.from_user.id
    db_user = get_user_data(user_id)

    if db_user:
        set_task_message(user_id, message.message_id + 1)
        tasks = db_user['tasks']

        if tasks:
            task_text = ''
            for key in tasks:
                task_text += key + ', '
            task_text = task_text[:-2]
        else:
            task_text = 'Нет установленного времени'
        text = f"Сообщения будут приходить: <b>{task_text}</b>."

        button_create = InlineKeyboardButton('Назначить время',  callback_data='create_task')
        button_delete = InlineKeyboardButton('Удалить время', callback_data='delete_task')
        keyboard = InlineKeyboardMarkup().add(button_create, button_delete)

        await message.answer(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await send_start(message)


@dp.callback_query_handler(lambda c: c.data == 'create_task')
async def create_task(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    db_user = get_user_data(user_id)

    await bot.edit_message_text('Введите время в формате "ЧЧ:ММ"', user_id, db_user['task_message'])
    await TimeTask.time_task.set()


@dp.message_handler(state=TimeTask.time_task)
async def set_time(message: types.Message, state: FSMContext):
    await state.update_data(time_task=message.text)
    state_data = await state.get_data()
    await state.finish()
    user_id = message.from_user.id
    db_user = get_user_data(user_id)

    user_time = state_data['time_task']
    time_split = user_time.split(':')
    if time_split[0].isdigit() and time_split[1].isdigit() and len(time_split) == 2:
        user_time_str = datetime.strptime(user_time, "%H:%M").strftime("%H:%M")
        utc = int(db_user['timezone'][4:])
        time_with_utc = datetime.strptime(user_time, "%H:%M") - timedelta(hours=utc)
        time_with_utc = time_with_utc.strftime('%H:%M')

        task = aioschedule.every().day.at(time_with_utc).do(send_news, user_id)
        db_user['tasks'][user_time_str] = task
        await bot.send_message(user_id, 'Время добавлено!')
    else:
        await bot.send_message(user_id, 'Время написано не по формату.')


@dp.callback_query_handler(lambda c: c.data == 'delete_task')
async def delete_task(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = db[user_id]
    tasks = data['tasks']

    keyboard = InlineKeyboardMarkup()
    for task in tasks:
        keyboard.add(InlineKeyboardButton(task, callback_data='delete:'+task))

    await bot.edit_message_text('Выберите время для удаления:', user_id, data['task_message'], reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data[:7] == 'delete:')
async def delete_task_num(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    data = db[user_id]
    tasks = data['tasks']
    task = callback_query.data[7:]

    aioschedule.cancel_job(tasks.pop(task))

    await bot.edit_message_text('Успешно!', user_id, data['task_message'])
'''


@dp.message_handler()
async def send_answer(message):
    db_user = get_user_data(message.from_user.id)
    if db_user:
        await send_news(message.from_user.id)
    else:
        await message.answer('Вы не зарегестрированы, введите комманду /start')


async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    await bot.set_my_commands(commands)

    aioschedule.every().day.at('2:30').do(send_news, ADMIN)
    aioschedule.every().day.at('7:00').do(send_news, ADMIN)
    aioschedule.every().day.at('11:00').do(send_news, ADMIN)
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(
        dispatcher=dp,
        on_startup=on_startup,
    )
