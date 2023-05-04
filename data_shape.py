import requests
import pytz
from datetime import datetime

tz = pytz.timezone('Asia/Omsk')

conditions = {
    'clear': 'ясно',
    'partly-cloudy': 'малооблачно',
    'cloudy': 'облачно',
    'overcast': 'пасмурно',
    'drizzle': 'морось',
    'light-rain': 'небольшой',
    'rain': 'дождь',
    'moderate-rain': 'умеренно',
    'heavy-rain': 'сильный',
    'continuous-heavy-rain': 'длительный',
    'showers': 'ливень',
    'wet-snow': 'дождь',
    'light-snow': 'небольшой',
    'snow': 'снег',
    'snow-showers': 'снегопад',
    'hail': 'град',
    'thunderstorm': 'гроза',
    'thunderstorm-with-rain': 'дождь',
    'thunderstorm-with-hail': 'гроза',
}


def get_data(yandex_api_key):
    # Получение данных о валюте
    try:
        response = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
        valute = response.json()['Valute']

        usd = valute['USD']['Value']
        usd = round(usd, 2)
        eur = valute['EUR']['Value']
        eur = round(eur, 2)
    except requests.exceptions.JSONDecodeError:
        usd = 'Ошибка'
        eur = 'Ошибка'

    # Получение данных о погоде
    try:
        response = requests.get('https://api.weather.yandex.ru/v2/forecast'
                                '?lat=55.000693&lon=73.240121&[lang=ru-RU]',
                                headers={'X-Yandex-API-Key': yandex_api_key})
        weather = response.json()

        city = weather['geo_object']['locality']['name']
        temp_fact = weather['fact']['temp']
        icon = f"https://yastatic.net/weather/i/icons/funky/dark/{weather['fact']['temp']}.svg"
        condition_fact = weather['fact']['condition']
        condition_fact = conditions[condition_fact]

    except requests.exceptions.JSONDecodeError:
        city = 'Ошибка'
        temp_fact = 'Ошибка'
        icon = 'Ошибка'
        condition_fact = 'Ошибка'

    # Формирование данных для вывода
    data = {
        'Время': datetime.now(tz).strftime('%H:%M'),
        'Дата': datetime.now(tz).strftime('%d.%m.%y'),
        'Курс доллара': usd,
        'Курс евро': eur,
        'Город': city,
        'Температура сейчас': temp_fact,
        'Иконка': icon,
        'Погодное описание': condition_fact,
    }

    return data
