import json

from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.users.db_hidden_esims import db_update_hidden_esims, db_get_hidden_esims

router = Router()


@router.callback_query(F.data.startswith("delete_esim_"))
async def delete_esim(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    iccid = callback.data.split("_")[-1]
    print(f"iccid: {iccid}")
    hidden_esims = db_get_hidden_esims(chat_id)
    print(f"hidden_esims: {hidden_esims}")
    if hidden_esims is not None and "esims" in hidden_esims:
        if hidden_esims not in hidden_esims["esims"]:
            hidden_esims["esims"].append(iccid)
    else:
        hidden_esims = {"esims": [iccid]}
    print(f"hidden_esims: {hidden_esims}")
    updated_json = json.dumps(hidden_esims)
    print(f"updated_json: {updated_json}")
    db_update_hidden_esims(chat_id, updated_json)
    await callback.message.edit_text(text="␡ Выбранная eSIM была *безвозвратно* удалена."
                                          "\nНе нужно ее пытаться продлить."
                                          "\nЗаведите новую с помощью команды /buy\_esim.")
