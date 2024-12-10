from datetime import datetime
from quart import Quart, request, render_template
import base64
import redis
import logging
import os
import httpx

from logging.handlers import RotatingFileHandler
from bnesim_api import BnesimApi
from config import Config
from db.db_bnesim_products import db_get_product_id
from db.db_buy_esim import db_get_emoji_from_two_tables, db_get_ru_name_from_two_tables
from link_for_marketplace.db_link import db_get_esim_data, db_switch_status_on_activated, db_update_iccid, db_get_iccid, \
    db_get_link_status, db_fill_date
from robokassa_api import handle_payment

# Инициализация Quart и Redis
app = Quart(__name__, static_folder='static')
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

CACHE_TTL = 120  # TTL для кэширования в секундах

# Формируем путь относительно текущего файла
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/error_page.log")

# Настройка логирования
log_formatter = logging.Formatter(
    "\n%(asctime)s - %(levelname)s - %(message)s => %(exc_info)s"
)

# Создаём обработчик для записи в файл
file_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(log_formatter)

# Настройка основного логгера
logger = logging.getLogger()
logger.setLevel(logging.ERROR)  # Логируем только ERROR и выше
logger.addHandler(file_handler)


async def generate_qr_code(data_url):
    """Асинхронная загрузка QR-кода по URL и конвертация в base64"""
    async with httpx.AsyncClient() as client:
        response = await client.get(data_url)
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


async def render_esim_page(country, gb_amount, ios_link, qr_code, instructions_link):
    """Рендеринг страницы eSIM"""
    return await render_template(
        'welcome.html',
        country=country,
        gb_amount=gb_amount,
        ios_universal_installation_link=ios_link,
        qr_code=qr_code,
        instructions_link=instructions_link,
    )


async def render_expired_page():
    """Рендеринг страницы истечения срока действия eSIM"""
    return await render_template(
        'expired_date_page.html',
        direct_bot_link=Config.BOT_LINK,
    )


async def render_error_page():
    """Рендеринг страницы с ошибкой"""
    return await render_template(
        'error_page.html',
    )


@app.route('/payment-result', methods=['GET', 'POST'])
async def payment_result():
    try:
        print("Request received:", request.method)
        print("Request data (form):", await request.form)  # Асинхронное получение данных

        if request.method == 'POST':
            post_data = await request.form
            await handle_payment(post_data)  # Нативно вызываем асинхронный метод

        return "OK", 200
    except Exception as e:
        logger.error(f"Error in /payment-result: {e}", exc_info=True)
        return "Internal Server Error", 500


@app.route('/<country>/<gb_amount>/<uuid>')
async def welcome_page(country: str, gb_amount: str, uuid: str):
    cache_key = f"esim:{country}:{gb_amount}:{uuid}"

    # Проверка кэша
    cached_page = redis_client.get(cache_key)
    if cached_page:
        return cached_page

    try:
        status = db_get_link_status(uuid)
        if status == "unactivated":
            db_fill_date(uuid)

        data = db_get_esim_data(uuid)
        if (datetime.now() - data[0]).days >= 30:
            return await render_expired_page()

        country_info = get_country_info(country)
        instructions_link = Config.QUESTIONS_LINK
        bnesim = BnesimApi()

        if data[1] == "unactivated":
            db_switch_status_on_activated(uuid)
            product_id = db_get_product_id(country, int(gb_amount))
            active_esim = await bnesim.activate_esim("558947250", product_id)
            db_update_iccid(active_esim["iccid"], uuid)

            gb_amount_display = f"{gb_amount}.0"
            ios_link = active_esim["ios_universal_installation_link"]
            qr_code = await generate_qr_code(active_esim["qr_code_url"])
        else:
            iccid = db_get_iccid(uuid)
            esim_info = await bnesim.get_esim_info(iccid)

            gb_amount_display = esim_info["remaining_data"]
            ios_link = esim_info["ios_link"]
            qr_code = await generate_qr_code(esim_info["qr_code_url"])

        rendered_page = await render_esim_page(country_info, gb_amount_display, ios_link, qr_code, instructions_link)
        cache_page(cache_key, CACHE_TTL, rendered_page)
        return rendered_page

    except Exception as e:
        # Логируем только ошибки
        logger.error(f"{uuid} : {str(e)}\n", exc_info=True)
        return await render_error_page(), 500


if __name__ == '__main__':
    app.run(ssl_context=('../cert.pem', '../key.pem'), host='0.0.0.0', port=443)