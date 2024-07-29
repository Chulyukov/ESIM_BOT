from db.db_connection import execute_query


def db_get_cli(chat_id):
    """Получаем cli"""
    result = execute_query("Ошибка при получении cli",
                           "SELECT cli FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None
