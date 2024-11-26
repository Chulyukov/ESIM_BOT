from db.db_connection import execute_query


def db_insert_esims(esims):
    """Добавляем новую ссылку для маркетплейса"""
    execute_query(
        "Ошибка при добавлении ссылки для маркетплейса",
        "INSERT INTO links (id, country, gb_amount, status) VALUES (%s, %s, %s, 'unactivated')",
        [(link["id"], link["country"], link["gb_amount"]) for link in esims],
        multiple=True
    )


def db_get_esim_data(esim_id):
    """Получаем данные esim"""
    result = execute_query(
        "Ошибка при получении данных по eSIM",
        "SELECT created_at, status FROM links WHERE id=%s",
        (esim_id,),
    )
    return result[0] if result else None


def db_get_link_status(esim_id):
    """Получаем статус ссылки"""
    result = execute_query(
        "Ошибка при получении статуса ссылки",
        "SELECT status FROM links WHERE id=%s",
        (esim_id,),
    )
    return result[0] if result else None


def db_switch_status_on_activated(esim_id):
    """Переключаем статус на activated"""
    execute_query("Ошибка при переключении статуса на activated",
                  "UPDATE links SET status='activated' WHERE id=%s",
                  (esim_id,))


def db_fill_date(esim_id):
    """Заполняем дату"""
    execute_query("Ошибка при переключении статуса на activated",
                  "UPDATE links SET created_at=NOW() WHERE id=%s",
                  (esim_id,))


def db_update_iccid(iccid, esim_id):
    """Записываем iccid созданной esim"""
    execute_query("Ошибка при записи iccid созданной esim",
                  "UPDATE links SET iccid=%s WHERE id=%s",
                  (iccid, esim_id,))


def db_get_iccid(esim_id):
    """Получаем iccid"""
    result = execute_query(
        "Ошибка при получении iccid",
        "SELECT iccid FROM links WHERE id=%s",
        (esim_id,),
    )
    return result[0][0] if result else None