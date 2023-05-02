import os
import requests
from datetime import datetime
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, executor, types
import asyncio
import aioschedule

from background import keep_alive

load_dotenv()

USERNAME = os.getenv('USERNAME')
TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


def get_data():
    # Получение данных о валюте
    try:
        valute = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
        valute = valute.json()['Valute']

        usd = valute['USD']['Value']
        usd = round(usd, 2)
        eur = valute['EUR']['Value']
        eur = round(usd, 2)
    except requests.exceptions.JSONDecodeError:
        usd = 'Ошибка'
        eur = 'Ошибка'

    data = {
        'Время': datetime.now().strftime('%H:%M'),
        'Дата': datetime.now().strftime('%d.%m.%y'),
        'Курс доллара': usd,
        'Курс евро': eur
    }

    return data


def convert_data():
    data = get_data()
    output = ''

    for key, item in data.items():
        output += f'{key}: {item}\n'
    output = output[:-1]

    return output


async def send_news():
    await bot.send_message(USERNAME, convert_data())


async def scheduler():
    aioschedule.every(3).seconds.do(send_news)
    # aioschedule.every().day.at('8:30').do(send_news)
    # aioschedule.every().day.at('13:00').do(send_news)
    # aioschedule.every().day.at('19:00').do(send_news)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    keep_alive()
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
