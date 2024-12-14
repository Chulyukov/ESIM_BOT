from flask import Flask, request
from logging.handlers import RotatingFileHandler

import logging
import logging

from robokassa_api import handle_payment  # Ваш метод обработки платежей

app = Flask(__name__)

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Обработчик для записи логов в файл
file_handler = RotatingFileHandler('app.log', maxBytes=10 * 1024 * 1024, backupCount=5)
file_handler.setLevel(logging.ERROR)

# Формат логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавляем обработчик в логгер
logger.addHandler(file_handler)


@app.route('/')
def home():
    return "Приложение работает!!!"


@app.route('/payment-result', methods=['POST'])
def payment_result():
    try:
        # Получаем данные из запроса
        post_data = request.form.to_dict()

        # Вызываем синхронный метод напрямую
        handle_payment(post_data)

        return "OK", 200
    except Exception as e:
        logger.error(f"Error in /payment-result: {e}", exc_info=True)
        return "Internal Server Error", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
