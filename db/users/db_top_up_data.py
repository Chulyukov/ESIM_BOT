import json

from db.db_connection import execute_query


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
    """Выставляем top_up_flag = 0"""
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
