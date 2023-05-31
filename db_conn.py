import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')


def update_user(tg_id, city, timezone, lat, lon):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cursor = conn.cursor()

    cursor.execute(f"SELECT tg_id FROM users WHERE tg_id = {tg_id};")
    answer = cursor.fetchall()

    if answer:
        cursor.execute(f"UPDATE users "
                       f"SET city = '{city}', timezone = '{timezone}', lat = {lat}, lon = {lon} "
                       f"WHERE tg_id = {tg_id};")
    else:
        cursor.execute(f"INSERT INTO users (tg_id, city, timezone, lat, lon) "
                       f"VALUES ({tg_id}, '{city}', '{timezone}', {lat}, {lon});")
    conn.commit()
    cursor.close()
    conn.close()


def get_user_data(tg_id):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cursor = conn.cursor()

    cursor.execute(f'SELECT tg_id, city, timezone, lat, lon FROM users WHERE tg_id = {tg_id};')
    answer = cursor.fetchall()
    cursor.close()
    conn.close()

    if answer:
        answer = answer[0]
        output = {
            'id': answer[0],
            'city': answer[1],
            'timezone': answer[2],
            'lat': answer[3],
            'lon': answer[4],
        }
    else:
        output = None

    return output
