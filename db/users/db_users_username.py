from db.db_connection import execute_query


def db_get_username(chat_id):
    """Получаем username пользователя"""
    result = execute_query("Ошибка при получении username",
                           "SELECT username FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None