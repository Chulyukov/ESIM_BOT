from db.db_connection import execute_query


def db_get_product_id(country, volume):
    """Получаем product_id"""
    result = execute_query("Ошибка при получении product_id",
                           "SELECT product_id FROM bnesim_products WHERE country = %s AND volume = %s",
                           (country, volume,))[0][0]
    return result if result else None


def db_get_username(chat_id):
    """Получаем username пользователя"""
    result = execute_query("Ошибка при получении username",
                           "SELECT username FROM users WHERE chat_id = %s",
                           (chat_id,))[0][0]
    return result if result else None


def db_update_cli(chat_id, cli):
    """Добавлям cli пользователю"""
    execute_query("Ошибка при добавлении cli",
                  "UPDATE users SET cli = %s WHERE chat_id = %s",
                  (cli, chat_id,))
