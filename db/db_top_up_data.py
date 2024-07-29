from db.db_connection import execute_query


def db_clean_top_up_data(chat_id):
    """Очищаем users.data"""
    execute_query("Ошибка при очищении users.data",
                  "UPDATE users SET top_up_data = '{}' WHERE chat_id = %s",
                  (chat_id,))


def db_update_top_up_data_iccid_and_country(chat_id, iccid, country):
    """Добавлям users.data.iccid и users.data.country"""
    execute_query("Ошибка при добавлении users.data.iccid",
                  "UPDATE users SET top_up_data = JSON_SET(IFNULL(top_up_data, '{}'), '$.iccid', %s, '$.country', %s) WHERE chat_id = %s",
                  (iccid, country, chat_id,))


def db_update_top_up_data_volume(chat_id, volume):
    """Добавлям users.data.volume"""
    execute_query("Ошибка при добавлении users.data.volume",
                  "UPDATE users SET top_up_data = JSON_SET(IFNULL(top_up_data, '{}'), '$.volume', %s) WHERE chat_id = %s",
                  (volume, chat_id,))


def db_get_top_up_data_country(chat_id):
    """Получаем users.data.country"""
    result = execute_query("Ошибка при получении users.data.country",
                           "SELECT JSON_EXTRACT(top_up_data, '$.country') AS country FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None


def db_get_all_top_up_data(chat_id):
    """Получаем users.data.iccid & country & volume"""
    result = execute_query("Ошибка при получении users.data.iccid",
                           "SELECT JSON_EXTRACT(top_up_data, '$.iccid', '$.country', '$.volume') FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None
