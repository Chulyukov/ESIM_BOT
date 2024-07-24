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
    except mysql.connector.Error as error:
        print(error)


def execute_query(err_msg, query, params=None):
    """Выполняем запрос с переподключением к бд при необходимости"""
    connection = get_database_connection()
    if connection is None:
        return None
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as error:
        print(err_msg)
        print(error)
        print()
        return None
    finally:
        connection.commit()
        cursor.close()
        connection.close()
