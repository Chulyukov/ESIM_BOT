from datetime import datetime
import requests
from flask import Flask, render_template
import qrcode
import io
import base64
import redis  # Импорт Redis

from bnesim_api import BnesimApi
from config import Config
from db.db_bnesim_products import db_get_product_id
from db.db_buy_esim import db_get_emoji_from_two_tables, db_get_ru_name_from_two_tables
from link_for_marketplace.db_link import db_get_esim_data, db_switch_status_on_activated, db_update_iccid, db_get_iccid

# Инициализация Flask
app = Flask(__name__, static_folder='static')

# Инициализация клиента Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


def generate_qr_code(data):
    """Генерация QR-кода в base64"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Сохранение QR-кода в память
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return img_base64


@app.route('/<country>/<gb_amount>/<uuid>')
def welcome_page(country: str, gb_amount: str, uuid: str):
    # Ключ для кэширования
    cache_key = f"esim:{country}:{gb_amount}:{uuid}"

    # Проверка в Redis
    cached_page = redis_client.get(cache_key)
    if cached_page:
        return cached_page  # Если страница есть в кэше, возвращаем ее

    # Если страницы нет в кэше
    data = db_get_esim_data(uuid)
    if (datetime.now() - data[0]).days < 30:
        instructions_link = Config.QUESTIONS_LINK  # TODO: обновить на актуальную ссылку
        emoji = db_get_emoji_from_two_tables(country)
        country = f"{db_get_ru_name_from_two_tables(country).capitalize()} {emoji}"
        bnesim = BnesimApi()
        if data[1] == "unactivated":
            # Основная логика для нового eSIM
            db_switch_status_on_activated(uuid)  # Переключаем статус
            product_id = db_get_product_id(country, int(gb_amount))
            active_esim = bnesim.activate_esim("558948184", product_id)
            db_update_iccid(active_esim["iccid"], uuid)
            gb_amount = f"{gb_amount} ГБ 📶"
            ios_universal_installation_link = active_esim["ios_universal_installation_link"]
            qr_code = base64.b64encode(active_esim["qr_code_url"]).decode("utf-8")
            # Рендеринг шаблона
            rendered_page = render_template(
                'welcome.html',
                country=country,
                gb_amount=gb_amount,
                ios_universal_installation_link=ios_universal_installation_link,
                qr_code=qr_code,
                instructions_link=instructions_link,
            )
            # Кэшируем страницу
            redis_client.setex(cache_key, 1800, rendered_page)  # TTL 1800 секунд
            return rendered_page
        else:
            # Логика для активированного eSIM
            iccid = db_get_iccid(uuid)
            esim_info = bnesim.get_esim_info(iccid)
            gb_amount = esim_info["remaining_data"]
            ios_universal_installation_link = esim_info["ios_link"]
            qr_code = base64.b64encode(io.BytesIO(requests.get(esim_info["qr_code_url"]).content).read()).decode("utf-8")
            rendered_page = render_template(
                'welcome.html',
                country=country,
                gb_amount=gb_amount,
                ios_universal_installation_link=ios_universal_installation_link,
                qr_code=qr_code,
                instructions_link=instructions_link,
            )
            # Кэшируем страницу
            redis_client.setex(cache_key, 1800, rendered_page)  # TTL 1800 секунд
            return rendered_page
    else:
        return render_template(
            'expired_date_page.html',
            direct_bot_link=Config.BOT_LINK,
        )


if __name__ == '__main__':
    app.run(ssl_context=('../cert.pem', '../key.pem'), host='0.0.0.0', port=443)
