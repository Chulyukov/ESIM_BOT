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


def db_get_all_coincidences_by_search(user_text):
    """Получаем все страны, совпавшие с поисковым запросом пользователя"""
    # Добавляем символы % для поиска вхождений
    countries_list = {}
    search_pattern = f"%{user_text}%"
    result = execute_query(
        "Ошибка при получении всех стран, совпавших с поисковым запросом пользователя",
        "SELECT name, ru_name, emoji FROM countries WHERE LOWER(name) LIKE %s OR LOWER(ru_name) LIKE %s",
        (search_pattern, search_pattern)
    )
    for country in result:
        countries_list[country[0]] = {"ru_name": country[1], "emoji": country[2]}
    return countries_list
