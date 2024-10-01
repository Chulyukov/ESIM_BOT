from db.db_connection import execute_query


def db_get_bnesim_products():
    """Получаем страны в таблицу"""
    result = execute_query("Ошибка при добавлении новой страны или при обновлении уже существующей",
                           "SELECT product_id, country, volume, price FROM bnesim_products")
    return {row[0]: {"country": row[1], "volume": row[2], "price": row[3]} for row in result}


def db_insert_bnesim_products(products: dict):
    """
    Вставляем, обновляем или удаляем записи в таблице bnesim_products.
    products — это словарь, где ключами являются product_id,
    а значениями — другой словарь с параметрами: country, volume, price.
    """

    # Подготовка данных для вставки
    values = []
    product_ids = []  # Список всех product_id для последующего удаления старых данных
    for product_id, details in products.items():
        country = details.get("country")
        volume = details.get("volume")
        price = details.get("price")
        values.append((product_id, country, volume, price))
        product_ids.append(product_id)

    # Если словарь пуст, выходим
    if not values:
        return

    # Формируем запрос на вставку или обновление записей
    insert_update_query = """
    INSERT INTO bnesim_products (product_id, country, volume, price)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        country = VALUES(country),
        volume = VALUES(volume),
        price = VALUES(price);
    """

    # Выполняем запрос с использованием executemany для вставки и обновления данных
    execute_query(
        "Ошибка при добавлении или обновлении продуктов",
        insert_update_query,
        params=values,
        multiple=True
    )

    # Формируем запрос на удаление записей, которых нет в новом наборе данных
    delete_query = """
    DELETE FROM bnesim_products
    WHERE product_id NOT IN (%s);
    """ % ','.join(['%s'] * len(product_ids))  # Формируем плейсхолдеры для списка product_ids

    # Выполняем запрос на удаление устаревших записей
    execute_query(
        "Ошибка при удалении старых продуктов",
        delete_query,
        params=tuple(product_ids)
    )


def db_get_price_data(country: str):
    """Получаем volume и price"""
    result = execute_query("Ошибка при получении volume и price",
                           "SELECT volume, price FROM bnesim_products WHERE country = %s",
                           (country,))
    return {data[0]: {"price": data[1]} for data in result}


def db_get_product_id(country, volume):
    """Получаем product_id"""
    result = execute_query("Ошибка при получении product_id",
                           "SELECT product_id FROM bnesim_products WHERE country = %s AND volume = %s",
                           (country, volume,))[0][0]
    return result if result else None
