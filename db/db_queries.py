import json
from types import NoneType

from db.db_connection import execute_query


def db_check_user_exist(chat_id):
    """Проверяем наличие пользователя в таблице"""
    result = execute_query("Ошибка при проверке наличия пользователя",
                           "SELECT count(*) FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None


def db_add_user(chat_id, username, activation_datetime):
    """Добавляем нового пользователя"""
    execute_query("Ошибка при добавлении нового пользователя",
                  "INSERT INTO users (chat_id, username, activation_datetime) VALUES (%s, %s, %s)",
                  (chat_id, username, activation_datetime,))


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
    """Получаем ru_name из одной таблицы
    (либо countries, либо regions: зависит от того, где присутствует направление)"""
    result = execute_query("Ошибка при получении emoji",
                           "SELECT ru_name FROM countries WHERE name = %s",
                           (country,))
    if not result:
        result = execute_query("Ошибка при получении emoji",
                               "SELECT ru_name FROM regions WHERE name = %s",
                               (country,))
    return result[0][0] if result else None


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


def db_update_cli(chat_id, cli):
    """Добавлям cli"""
    execute_query("Ошибка при добавлении cli",
                  "UPDATE users SET cli = %s WHERE chat_id = %s",
                  (cli, chat_id,))


def db_get_cli(chat_id):
    """Получаем cli"""
    result = execute_query("Ошибка при получении cli",
                           "SELECT cli FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None


def db_get_all_cli():
    """Получаем все имеющиеся cli"""
    result = execute_query("Ошибка при получении всех cli",
                           "SELECT chat_id, cli FROM users WHERE cli IS NOT NULL")
    return result if result else None


def db_clean_data(chat_id):
    """Очищаем users.data"""
    execute_query("Ошибка при очищении users.data",
                  "UPDATE users SET data = '{}' WHERE chat_id = %s",
                  (chat_id,))


def db_update_data_country(chat_id, country):
    """Добавлям users.data.country"""
    execute_query("Ошибка при добавлении users.data.country",
                  "UPDATE users SET data = JSON_SET(IFNULL(data, '{}'), '$.country', %s) WHERE chat_id = %s",
                  (country, chat_id,))


def db_update_data_volume(chat_id, volume):
    """Добавлям users.data.volume"""
    execute_query("Ошибка при добавлении users.data.volume",
                  "UPDATE users SET data = JSON_SET(IFNULL(data, '{}'), '$.volume', %s) WHERE chat_id = %s",
                  (volume, chat_id,))


def db_get_data_volume(chat_id):
    """Получаем users.data.volume"""
    result = execute_query("Ошибка при получении users.data.volume",
                           "SELECT JSON_EXTRACT(data, '$.volume') AS volume FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None


def db_get_data_country(chat_id):
    """Получаем users.data.country"""
    result = json.loads(execute_query("Ошибка при получении users.data.country",
                                      "SELECT data FROM users WHERE chat_id = %s",
                                      (chat_id,))[0][0])
    return result["country"].replace("\"", "") if result else None


def db_get_all_data(chat_id):
    """Получаем users.data.country & volume"""
    result = execute_query("Ошибка при получении users.data.country & volume",
                           "SELECT data FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return json.loads(result) if result else None


def db_update_hidden_esims(chat_id, iccids_json):
    """Добавлям hidden_esims"""
    execute_query("Ошибка при добавлении hidden_esims",
                  "UPDATE users SET hidden_esims = %s WHERE chat_id = %s",
                  (iccids_json, chat_id,))


def db_get_hidden_esims(chat_id):
    """Получаем hidden_esims"""
    result = execute_query("Ошибка при получении hidden_esims",
                           "SELECT hidden_esims FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return json.loads(result) if not isinstance(result, NoneType) else None


def db_save_invoice_user(invoice_id, chat_id, username, date):
    execute_query("Ошибка при добавлении записи в payments",
                  "INSERT INTO payments (invoice_id, chat_id, username, date) VALUES (%s, %s, %s, %s)",
                  (invoice_id, chat_id, username, date,))


def db_get_chat_id_by_invoice_id(invoice_id):
    result = execute_query("Ошибка при получении chat_id по invoice_id",
                           "SELECT chat_id FROM payments WHERE invoice_id = %s",
                           (invoice_id,))[0][0]
    return result if result else None


def db_get_username_by_invoice_id(invoice_id):
    result = execute_query("Ошибка при получении username по invoice_id",
                           "SELECT username FROM payments WHERE invoice_id = %s",
                           (invoice_id,))[0][0]
    return result if result else None


def db_update_payment_status(invoice_id, status):
    execute_query("Ошибка при изменении статуса в payments",
                  "UPDATE payments SET status = %s WHERE invoice_id = %s",
                  (status, invoice_id,))


def db_clean_top_up_data(chat_id):
    """Очищаем users.data"""
    execute_query("Ошибка при очищении users.data",
                  "UPDATE users SET top_up_data = '{}' WHERE chat_id = %s",
                  (chat_id,))


def db_update_top_up_data_iccid_and_country(chat_id, iccid, country):
    """Добавлям users.data.iccid и users.data.country"""
    execute_query("Ошибка при добавлении users.data.iccid",
                  "UPDATE users"
                  " SET top_up_data = JSON_SET(IFNULL(top_up_data, '{}'), '$.iccid', %s, '$.country', %s)"
                  " WHERE chat_id = %s",
                  (iccid, country, chat_id,))


def db_update_top_up_data_volume(chat_id, volume):
    """Добавлям users.data.volume"""
    execute_query("Ошибка при добавлении users.data.volume",
                  "UPDATE users"
                  " SET top_up_data = JSON_SET(IFNULL(top_up_data, '{}'), '$.volume', %s) WHERE chat_id = %s",
                  (volume, chat_id,))


def db_update_top_up_flag_true(chat_id):
    """Выставляем top_up_flag = 1"""
    execute_query("Ошибка при добавлении top_up_flag",
                  "UPDATE users SET top_up_flag = 1 WHERE chat_id = %s",
                  (chat_id,))


def db_update_top_up_flag_false(chat_id):
    """Выставляем top_up_flag = 0"""
    execute_query("Ошибка при выставлении top_up_flag = 0",
                  "UPDATE users SET top_up_flag = 0 WHERE chat_id = %s",
                  (chat_id,))


def db_get_top_up_flag(chat_id):
    """Получаем top_up_flag"""
    result = execute_query("Ошибка при получении top_up_flag",
                           "SELECT top_up_flag FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None


def db_get_top_up_data_country(chat_id):
    """Получаем users.data.country"""
    result = json.loads(execute_query("Ошибка при получении users.data.country",
                                      "SELECT top_up_data FROM users WHERE chat_id = %s",
                                      (chat_id,))[0][0])
    return result["country"].replace("\"", "") if result else None


def db_get_all_top_up_data(chat_id):
    """Получаем users.data.iccid & country & volume"""
    result = execute_query("Ошибка при получении users.data.iccid",
                           "SELECT top_up_data FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]

    return json.loads(result) if result else None


def db_get_username(chat_id):
    result = execute_query("Ошибка при получении username",
                           "SELECT username FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None


def db_get_regions():
    """Получаем регионы и их эмодзи, пропуская pages_to_skip * 20 стран"""
    query = """
    SELECT name, ru_name, emoji
    FROM regions
    WHERE name != 'global'
    ORDER BY name
    """

    result = execute_query("Ошибка при получении регионов", query, ())

    return [(row[0], row[1], row[2]) for row in result] if result else []


def db_get_20_countries(pages_to_skip):
    """Получаем 20 стран и их эмодзи, пропуская pages_to_skip * 20 стран"""
    # Определяем смещение на основе количества страниц, которые нужно пропустить
    offset = pages_to_skip * 20

    # SQL-запрос для сортировки и получения стран с ограничением и эмодзи
    query = """
    SELECT name, ru_name, emoji
    FROM countries
    ORDER BY name
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


def db_get_pay_pic_link(name):
    """Получаем pay_pic_link"""
    result = execute_query("Ошибка при получении pay_pic_link",
                           "SELECT pay_pic_link FROM countries WHERE name = %s",
                           (name,))
    return result[0][0] if result else None
