import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from db_conn import get_user

load_dotenv()

YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')

with open('cities.json', 'r', encoding='UTF-8') as f:
    cities = json.load(f)

# Перевод всех состояний погоды с Яндекса https://yandex.ru/dev/weather/doc/dg/concepts/forecast-test.html
conditions = {
    'clear': 'ясно',
    'partly-cloudy': 'малооблачно',
    'cloudy': 'облачно',
    'overcast': 'пасмурно',
    'drizzle': 'морось',
    'light-rain': 'небольшой дождь',
    'rain': 'дождь',
    'moderate-rain': 'умеренно',
    'heavy-rain': 'сильный',
    'continuous-heavy-rain': 'длительный',
    'showers': 'ливень',
    'wet-snow': 'мокрый снег',
    'light-snow': 'небольшой снег',
    'snow': 'снег',
    'snow-showers': 'снегопад',
    'hail': 'град',
    'thunderstorm': 'гроза',
    'thunderstorm-with-rain': 'дождь',
    'thunderstorm-with-hail': 'гроза',
}

# Названия картинок для всех состояний погоды
condition_photo = {
    'clear': 'clear',
    'partly-cloudy': 'partly-cloudy',
    'cloudy': 'cloudy',
    'overcast': 'overcast',
    'drizzle': 'rain',
    'light-rain': 'rain',
    'rain': 'rain',
    'moderate-rain': 'rain',
    'heavy-rain': 'rain',
    'continuous-heavy-rain': 'rain',
    'showers': 'rain',
    'wet-snow': 'snow',
    'light-snow': 'snow',
    'snow': 'snow',
    'snow-showers': 'snow',
    'hail': 'hail',
    'thunderstorm': 'thunderstorm',
    'thunderstorm-with-rain': 'thunderstorm-rain',
    'thunderstorm-with-hail': 'thunderstorm-rain',
}


def get_data(user_id):
    user_data = get_user(user_id)
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
        usd, usd_changes, eur, eur_changes = 'Ошибка' * 4

    # Получение данных о погоде
    try:
        response = requests.get(f"https://api.weather.yandex.ru/v2/informers?"
                                f"lat={user_data['lat']}&"
                                f"lon={user_data['lon']}&"
                                f"[lang=ru-RU]",
                                headers={'X-Yandex-API-Key': YANDEX_API_KEY})
        weather = response.json()

        try:
            forecasts = []
            forecasts_request = weather['forecasts'][1:]
            for i in forecasts_request:
                date = datetime.strptime(i['date'], '%Y-%m-%d')
                day_in_fc = {
                    'date': date.strftime('%d.%m'),
                    'day': i['parts']['day']['temp_avg'],
                    'night': i['parts']['night']['temp_avg']
                }
                forecasts.append(day_in_fc)
        except KeyError:
            forecasts = None

        temp_fact = weather['fact']['temp']
        condition_fact = weather['fact']['condition']
        photo = condition_photo[condition_fact]
        condition_fact = conditions[condition_fact]

    except requests.exceptions.JSONDecodeError:
        temp_fact, condition_fact = ['Ошибка соединения' for i in range(2)]
        forecasts = None
        photo = 'error'

    # Формирование даты
    utc = int(user_data['timezone'][4:])
    tz = timedelta(hours=utc)
    dt = datetime.now() + tz

    data = {
        'time': dt.strftime('%H:%M'),
        'date': dt.strftime('%d.%m.%y'),
        'usd': usd,
        'usd_changes': usd_changes,
        'eur': eur,
        'eur_changes': eur_changes,
        'photo': photo,
        'temp_fact': temp_fact,
        'condition_fact': condition_fact,
        'forecasts': forecasts,
    }

    return data


def search_city(name):
    for obj in cities:
        if name.lower() == obj['city'].lower():
            return obj
