import json

from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.users.db_hidden_esims import db_update_hidden_esims, db_get_hidden_esims

router = Router()


@router.callback_query(F.data.startswith("delete_esim_"))
async def delete_esim(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    iccid = callback.data.split("_")[-1]
    hidden_esims = db_get_hidden_esims(chat_id)

    if hidden_esims is not None and "esims" in hidden_esims:
        if iccid not in hidden_esims["esims"]:
            hidden_esims["esims"].append(iccid)
            await callback.message.edit_text(text="␡ Выбранная eSIM была *безвозвратно* удалена."
                                                  "\nНе нужно ее пытаться продлить."
                                                  "\nЗаведите новую с помощью команды /buy\_esim.")
        else:
            await callback.message.edit_text(text="␡ Выбранная eSIM уже была *безвозвратно* удалена."
                                                  "\nЗаведите новую с помощью команды /buy\_esim.")
    else:
        hidden_esims = {"esims": [iccid]}
        await callback.message.edit_text(text="␡ Выбранная eSIM уже была *безвозвратно* удалена."
                                              "\nЗаведите новую с помощью команды /buy\_esim.")
    updated_json = json.dumps(hidden_esims)
    db_update_hidden_esims(chat_id, updated_json)
