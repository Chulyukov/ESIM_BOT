from db.db_connection import execute_query


def db_get_20_countries(pages_to_skip):
    """Получаем 20 стран и их эмодзи, пропуская pages_to_skip * 20 стран"""
    # Определяем смещение на основе количества страниц, которые нужно пропустить
    offset = pages_to_skip * 20

    # SQL-запрос для сортировки и получения стран с ограничением и эмодзи
    query = """
    SELECT name, ru_name, emoji
    FROM countries
    ORDER BY name ASC
    LIMIT 20 OFFSET %s
    """

    # Выполняем запрос, передавая смещение
    result = execute_query("Ошибка при получении стран", query, (offset,))

    # Возвращаем список кортежей (country, emoji)
    return [(row[0], row[1], row[2]) for row in result] if result else []
