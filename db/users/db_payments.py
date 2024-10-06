from db.db_connection import execute_query


def db_save_invoice_user(invoice_id, chat_id, username, date):
    execute_query("Ошибка при добавлении записи в payments",
                  "INSERT INTO payments (invoice_id, chat_id, username, date) VALUES (%s, %s, %s, %s)",
                  (invoice_id, chat_id, username, date,))


def db_get_chat_id_by_invoice_id(invoice_id):
    result = execute_query("Ошибка при получении chat_id по invoice_id",
                           "SELECT chat_id FROM payments WHERE invoice_id = %s",
                           (invoice_id,))[0][0]
    return result if result else None


def db_get_username_by_invoice_id(invoice_id):
    result = execute_query("Ошибка при получении username по invoice_id",
                           "SELECT username FROM payments WHERE invoice_id = %s",
                           (invoice_id,))[0][0]
    return result if result else None


def db_update_payment_status(invoice_id, status):
    execute_query("Ошибка при изменении статуса в payments",
                  "UPDATE payments SET status = %s WHERE invoice_id = %s",
                  (status, invoice_id,))
