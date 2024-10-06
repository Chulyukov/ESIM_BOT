from db.db_connection import execute_query


def db_get_emoji_from_two_tables(country):
    """Получаем emoji из одной таблицы (либо countries, либо regions: зависит от того, где присутствует направление)"""
    result = execute_query("Ошибка при получении emoji",
                           "SELECT emoji FROM countries WHERE name = %s",
                           (country,))
    if not result:
        result = execute_query("Ошибка при получении emoji",
                               "SELECT emoji FROM regions WHERE name = %s",
                               (country,))
    return result[0][0] if result else None


def db_get_ru_name_from_two_tables(country):
    """Получаем ru_name из одной таблицы (либо countries, либо regions: зависит от того, где присутствует направление)"""
    result = execute_query("Ошибка при получении emoji",
                           "SELECT ru_name FROM countries WHERE name = %s",
                           (country,))
    if not result:
        result = execute_query("Ошибка при получении emoji",
                               "SELECT ru_name FROM regions WHERE name = %s",
                               (country,))
    return result[0][0] if result else None
