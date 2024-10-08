import asyncio
import os
from datetime import datetime

from aiogram.types import FSInputFile  # Импортируем класс FSInputFile для отправки файла

from bnesim_api import BnesimApi
from config import Config
from db.db_bnesim_products import db_get_bnesim_products


async def update_products():
    bnesim = BnesimApi()
    old_data = db_get_bnesim_products()  # Старые данные из базы
    new_data = bnesim.get_products_catalog()  # Новые данные из API
    result_text = "Проверка update_bnesim_products была произведена успешно.\n\n"

    # 1. Преобразуем данные в формат с ключом по (Country, Volume) для лучшего сравнения
    old_data_by_country_volume = {(v['country'], v['volume']): {'product_id': k, **v} for k, v in old_data.items()}
    new_data_by_country_volume = {(v['country'], v['volume']): {'product_id': k, **v} for k, v in new_data.items()}

    # 2. Проверяем добавленные и изменённые продукты
    for key in new_data_by_country_volume.keys():
        new_value = new_data_by_country_volume[key]
        old_value = old_data_by_country_volume.get(key)

        if old_value is None:
            # Новая запись
            result_text += f"Добавлен новый продукт:\n    Country: {new_value['country']}, Volume: {new_value['volume']}, Product ID: {new_value['product_id']}, Price: {new_value['price']}\n\n"
        else:
            # Существующая запись: проверяем изменения
            changes = []
            if old_value['product_id'] != new_value['product_id']:
                changes.append(f"Product ID: {old_value['product_id']} -> {new_value['product_id']}")
            if old_value['price'] != new_value['price']:
                changes.append(f"Цена: {old_value['price']} -> {new_value['price']}")

            if changes:
                result_text += f"Изменения для продукта Country: {new_value['country']}, Volume: {new_value['volume']}:\n"
                for change in changes:
                    result_text += f"    {change}\n"
                result_text += "\n"

    # 3. Проверяем удалённые продукты (которые были в старых данных, но отсутствуют в новых)
    for key in old_data_by_country_volume.keys() - new_data_by_country_volume.keys():
        old_value = old_data_by_country_volume[key]
        result_text += f"Удалён продукт:\n    Country: {old_value['country']}, Volume: {old_value['volume']}, Product ID: {old_value['product_id']}, Price: {old_value['price']}\n\n"

    # Сохраняем результат в файл, если текст слишком большой для отправки в сообщение
    if len(result_text) > 4000:  # Лимит сообщения в Telegram — 4096 символов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"bnesim_products_update_{timestamp}.txt"
        file_path = os.path.join('/tmp', file_name)  # Сохраняем временно в директории /tmp

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(result_text)

        # Отправляем файл через Телеграм
        try:
            input_file = FSInputFile(file_path, filename=file_name)  # Создаём объект FSInputFile
            await Config.BOT.send_document(chat_id="1547142782", document=input_file)
        except Exception as e:
            print(f"Ошибка при отправке файла пользователю с chat_id=1547142782: {e}")
        finally:
            # Удаляем временный файл после отправки
            os.remove(file_path)
    else:
        # Если текст не слишком большой, отправляем его как сообщение
        try:
            await Config.BOT.send_message("1547142782", result_text)
        except Exception as e:
            print(f"Произошла ошибка при отправке сообщения пользователю с chat_id=1547142782: {e}")


# Запуск асинхронной функции
asyncio.run(update_products())