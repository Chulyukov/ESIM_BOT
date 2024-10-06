from db.db_connection import execute_query


def db_get_regions():
    """Получаем регионы и их эмодзи, пропуская pages_to_skip * 20 стран"""
    query = """
    SELECT name, ru_name, emoji
    FROM regions
    WHERE name != 'global'
    ORDER BY name ASC
    """

    result = execute_query("Ошибка при получении регионов", query, ())

    return [(row[0], row[1], row[2]) for row in result] if result else []

