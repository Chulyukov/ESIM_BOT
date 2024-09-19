from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.users.db_hidden_esims import db_update_hidden_esims

router = Router()


@router.callback_query(F.data.startswith('delete_esim_'))
async def delete_esim(callback: CallbackQuery):
    db_update_hidden_esims(callback.message.chat.id, f"{callback.data.split("_")[-1]}, ")
    await callback.message.edit_text(text="␡ Выбранная eSIM была *безвозвратно* удалена.")
