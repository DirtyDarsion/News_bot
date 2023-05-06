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
        usd_prev = valute['USD']['Previous']
        if usd > usd_prev:
            usd_changes = '⬆'
        else:
            usd_changes = '⬇'
        usd = round(usd, 2)

        eur = valute['EUR']['Value']
        eur_prev = valute['EUR']['Previous']
        if eur > eur_prev:
            eur_changes = '⬆'
        else:
            eur_changes = '⬇'
        eur = round(eur, 2)
    except requests.exceptions.JSONDecodeError:
        usd = 'Ошибка'
        usd_changes = 'Ошибка'
        eur = 'Ошибка'
        eur_changes = 'Ошибка'

    # Получение данных о погоде
    try:
        response = requests.get('https://api.weather.yandex.ru/v2/forecast'
                                '?lat=55.000693&lon=73.240121&[lang=ru-RU]',
                                headers={'X-Yandex-API-Key': yandex_api_key})
        weather = response.json()

        city = weather['geo_object']['locality']['name']
        temp_fact = weather['fact']['temp']
        icon = f"https://yastatic.net/weather/i/icons/funky/dark/{weather['fact']['icon']}.svg"
        condition_fact = weather['fact']['condition']
        condition_fact = conditions[condition_fact]

    except requests.exceptions.JSONDecodeError:
        city = 'Ошибка'
        temp_fact = 'Ошибка'
        icon = 'Ошибка'
        condition_fact = 'Ошибка'

    # Формирование данных для вывода
    data = {
        'time': datetime.now(tz).strftime('%H:%M'),
        'date': datetime.now(tz).strftime('%d.%m.%y'),
        'usd': usd,
        'usd_changes': usd_changes,
        'eur': eur,
        'eur_changes': eur_changes,
        'city': city,
        'temp_fact': temp_fact,
        'icon': icon,
        'condition_fact': condition_fact,
    }

    return data
