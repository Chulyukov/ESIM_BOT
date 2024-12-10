import json
from aiogram import Router, F
from aiogram.types import CallbackQuery
from db.db_queries import db_get_hidden_esims, db_update_hidden_esims

router = Router()

# Константы для текстов сообщений
ESIM_DELETED_TEXT = (
    "␡ Выбранная eSIM была *безвозвратно* удалена."
    "\nНе нужно ее пытаться продлить."
    "\nЗаведите новую с помощью команды /buy\\_esim."
)
ESIM_ALREADY_DELETED_TEXT = (
    "␡ Выбранная eSIM уже была *безвозвратно* удалена."
    "\nЗаведите новую с помощью команды /buy\\_esim."
)


@router.callback_query(F.data.startswith("delete_esim_"))
async def delete_esim(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    iccid = callback.data.split("_")[-1]

    # Получаем список скрытых eSIM
    hidden_esims = db_get_hidden_esims(chat_id)
    if hidden_esims is None or "esims" not in hidden_esims:
        hidden_esims = {"esims": []}

    # Проверяем, была ли уже удалена eSIM
    if iccid in hidden_esims["esims"]:
        message_text = ESIM_ALREADY_DELETED_TEXT
    else:
        hidden_esims["esims"].append(iccid)
        message_text = ESIM_DELETED_TEXT

    # Обновляем данные в базе и отправляем ответ пользователю
    db_update_hidden_esims(chat_id, json.dumps(hidden_esims))
    await callback.message.edit_text(text=message_text)