import mysql.connector

from config import Config


def get_database_connection():
    """Подключаемся к бд, берем кредо из config"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASS,
            database=Config.DB_NAME
        )
        return connection
    except mysql.connector.Error as err:
        print("Проблема с подключением к БД: ", err)


def execute_query(err_msg, query, params=None, multiple=False):
    """
    Выполняем запрос с переподключением к БД при необходимости.
    multiple: Если True, используем executemany для обработки нескольких строк.
    """
    connection = get_database_connection()
    if connection is None:
        return None
    cursor = connection.cursor()
    try:
        if multiple:
            cursor.executemany(query, params)  # Для множества значений
        else:
            cursor.execute(query, params)     # Для одного запроса
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        print(err_msg, ':', err)
        return None
    finally:
        connection.commit()
        cursor.close()
        connection.close()
