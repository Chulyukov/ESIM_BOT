from db.db_connection import execute_query


def db_get_pay_pic_link(name):
    """Получаем pay_pic_link"""
    result = execute_query("Ошибка при получении pay_pic_link",
                           "SELECT pay_pic_link FROM countries WHERE name = %s",
                           (name,))
    return result[0][0] if result else None
