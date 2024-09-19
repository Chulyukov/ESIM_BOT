from db.db_connection import execute_query


def db_update_hidden_esims(chat_id, iccid):
    """Добавлям hidden_esims"""
    execute_query("Ошибка при добавлении hidden_esims",
                  "UPDATE users SET hidden_esims = %s WHERE chat_id = %s",
                  (iccid, chat_id,))


def db_get_hidden_esims(chat_id):
    """Получаем hidden_esims"""
    result = execute_query("Ошибка при получении hidden_esims",
                           "SELECT hidden_esims FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result.split(", ") if result else None
