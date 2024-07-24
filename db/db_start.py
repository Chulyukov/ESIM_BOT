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
