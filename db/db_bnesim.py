from db.db_connection import execute_query


def db_insert_bnesim_products(id: str, product_name: str, volume: int):
    """Добавляем новые страны в таблицу"""
    execute_query("Ошибка при добавлении новой страны или при обновлении уже существующей",
                           "INSERT INTO bnesim_products (product_id, country, volume)"
                           " VALUES (%s, %s, %s)"
                           " ON DUPLICATE KEY UPDATE"
                           " country = VALUES(country), volume = VALUES(volume);",
                           (id, product_name, volume))

