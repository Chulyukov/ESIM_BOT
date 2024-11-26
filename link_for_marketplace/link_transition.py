from datetime import datetime
import requests
from flask import Flask, render_template
import base64
import redis

from bnesim_api import BnesimApi
from config import Config
from db.db_bnesim_products import db_get_product_id
from db.db_buy_esim import db_get_emoji_from_two_tables, db_get_ru_name_from_two_tables
from link_for_marketplace.db_link import db_get_esim_data, db_switch_status_on_activated, db_update_iccid, db_get_iccid, \
    db_get_link_status, db_fill_date

# Инициализация Flask и Redis
app = Flask(__name__, static_folder='static')
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

CACHE_TTL = 1800  # TTL для кэширования в секундах


def generate_qr_code(data_url):
    """Загрузка QR-кода по URL и конвертация в base64"""
    response = requests.get(data_url)
    response.raise_for_status()  # Обработка ошибок загрузки
    return base64.b64encode(response.content).decode("utf-8")


def get_country_info(country):
    """Получение информации о стране (название и эмодзи)"""
    emoji = db_get_emoji_from_two_tables(country)
    country_name = db_get_ru_name_from_two_tables(country).capitalize()
    return f"{country_name} {emoji}"


def cache_page(key, ttl, page_content):
    """Кэширование страницы"""
    redis_client.setex(key, ttl, page_content)


def render_esim_page(country, gb_amount, ios_link, qr_code, instructions_link):
    """Рендеринг страницы eSIM"""
    return render_template(
        'welcome.html',
        country=country,
        gb_amount=gb_amount,
        ios_universal_installation_link=ios_link,
        qr_code=qr_code,
        instructions_link=instructions_link,
    )


def render_expired_page():
    """Рендеринг страницы истечения срока действия eSIM"""
    return render_template(
        'expired_date_page.html',
        direct_bot_link=Config.BOT_LINK,
    )


@app.route('/<country>/<gb_amount>/<uuid>')
def welcome_page(country: str, gb_amount: str, uuid: str):
    cache_key = f"esim:{country}:{gb_amount}:{uuid}"

    # Проверка кэша
    cached_page = redis_client.get(cache_key)
    if cached_page:
        return cached_page

    try:
        # Проверка статуса ссылки
        status = db_get_link_status(uuid)
        if status == "unactivated":
            db_fill_date(uuid)

        # Получение данных eSIM
        data = db_get_esim_data(uuid)
        if (datetime.now() - data[0]).days >= 30:
            return render_expired_page()

        # Получение информации о стране
        country_info = get_country_info(country)
        instructions_link = Config.QUESTIONS_LINK
        bnesim = BnesimApi()

        # Логика для неактивированного eSIM
        if data[1] == "unactivated":
            db_switch_status_on_activated(uuid)
            product_id = db_get_product_id(country, int(gb_amount))
            active_esim = bnesim.activate_esim("558948184", product_id)
            db_update_iccid(active_esim["iccid"], uuid)

            gb_amount_display = f"{gb_amount}.0"
            ios_link = active_esim["ios_universal_installation_link"]
            qr_code = generate_qr_code(active_esim["qr_code_url"])
        else:
            # Логика для активированного eSIM
            iccid = db_get_iccid(uuid)
            esim_info = bnesim.get_esim_info(iccid)

            gb_amount_display = esim_info["remaining_data"]
            ios_link = esim_info["ios_link"]
            qr_code = generate_qr_code(esim_info["qr_code_url"])

        # Рендеринг и кэширование страницы
        rendered_page = render_esim_page(country_info, gb_amount_display, ios_link, qr_code, instructions_link)
        cache_page(cache_key, CACHE_TTL, rendered_page)
        return rendered_page

    except Exception as e:
        return f"Ошибка: {str(e)}\n\nПросьба прислать скриншот в поддержку Telegram https://t.me/esim_unity_support или в WhatsApp https://wa.me/22943343372", 500


if __name__ == '__main__':
    app.run(ssl_context=('../cert.pem', '../key.pem'), host='0.0.0.0', port=443)