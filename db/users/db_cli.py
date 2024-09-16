from db.db_connection import execute_query


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
