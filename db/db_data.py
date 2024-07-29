from db.db_connection import execute_query


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
    result = execute_query("Ошибка при получении users.data.country",
                           "SELECT JSON_EXTRACT(data, '$.country') AS country FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None


def db_get_all_data(chat_id):
    """Получаем users.data.country & volume"""
    result = execute_query("Ошибка при получении users.data.country & volume",
                           "SELECT JSON_EXTRACT(data, '$.country', '$.volume') FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None
