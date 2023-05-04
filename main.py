import os
import requests
from datetime import datetime
from dotenv import load_dotenv

import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, executor, types

from web_server import keep_alive
from data_shape import get_data

load_dotenv()

USERNAME = os.getenv('USERNAME')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


async def send_news():
    data = get_data(YANDEX_API_KEY)

    text = ''
    for key, item in data.items():
        text += f'{key}: {item}\n'
    text = text[:-1]

    await bot.send_message(USERNAME, text)


@dp.message_handler()
async def send_answer(message):
    await send_news()


async def scheduler():
    aioschedule.every().day.at('2:30').do(send_news)
    aioschedule.every().day.at('7:00').do(send_news)
    aioschedule.every().day.at('11:00').do(send_news)
    aioschedule.every().day.at('17:45').do(send_news)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    keep_alive()
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
