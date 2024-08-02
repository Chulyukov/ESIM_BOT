from db.db_connection import execute_query


def db_get_bnesim_products():
    """Получаем страны в таблицу"""
    result = execute_query("Ошибка при добавлении новой страны или при обновлении уже существующей",
                           "SELECT product_id, country, volume, price FROM bnesim_products")
    return {row[0]: {"country": row[1], "volume": row[2], "price": row[3]} for row in result}


def db_insert_bnesim_products(id: str, country: str, volume: int, price: str):
    """Добавляем новые страны в таблицу"""
    execute_query("Ошибка при добавлении новой страны или при обновлении уже существующей",
                           "INSERT INTO bnesim_products (product_id, country, volume, price)"
                           " VALUES (%s, %s, %s, %s)"
                           " ON DUPLICATE KEY UPDATE"
                           " country = VALUES(country), volume = VALUES(volume), price = VALUES(price)",
                           (id, country, volume, price))


def db_get_price_data(country: str):
    """Получаем volume, price и percentage_of_profit"""
    result = execute_query("Ошибка при получении percentage_of_profit",
                           "SELECT volume, percentage_of_profit, price FROM bnesim_products WHERE country = %s",
                           (country,))
    return {data[0]: {"percentage_of_profit": data[1], "price": data[2]} for data in result}


