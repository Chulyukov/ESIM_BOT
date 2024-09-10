import asyncio

from bnesim_api import BnesimApi
from config import Config
from db.db_bnesim_products import db_get_bnesim_products


async def update_products():
    text = "Продукты без изменений"
    bnesim = BnesimApi()
    old_data = db_get_bnesim_products()
    new_data = bnesim.get_products_catalog()

    for product_id in new_data.keys():
        old_value = old_data.get(product_id)
        new_value = new_data.get(product_id)

        if old_value != new_value:
            text = f"Изменения для product\_id {product_id}:"
            if old_value is None:
                text += f"\n\nНовая запись: {new_value}"
            elif new_value is None:
                text += f"\nУдалена запись: {old_value}"
            else:
                text += f"\nСтарое значение: {old_value}"
                text += f"\nНовое значение: {new_value}"
    try:
        await Config.BOT.send_message("1547142782", text)
    except Exception as e:
        print(f"Произошла ошибка при отправке сообщения пользователю с chat_id=1547142782: {e}")

asyncio.run(update_products())
