import asyncio

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from async_bnesim_api import AsyncBnesimApi
from bnesim_api import BnesimApi
from config import Config
from db.users.db_cli import db_get_all_cli
from db.users.db_hidden_esims import db_get_hidden_esims

bnesim_api = BnesimApi()
users_list = db_get_all_cli()


async def send_remaining_info():
    for user in users_list:
        hidden_esims = db_get_hidden_esims(user[0])
        iccids_dict = bnesim_api.get_iccids_of_user(user[1])
        if iccids_dict["length"] > 0:
            for iccid in iccids_dict["iccids"]:
                if hidden_esims is not None and iccid in hidden_esims["esims"]:
                    continue
                esim_info = bnesim_api.get_esim_info(iccid)
                if esim_info is not None and esim_info['remaining_data'] <= 1.0:
                    kb = InlineKeyboardBuilder().add(
                        InlineKeyboardButton(text="Продлить интернет", callback_data="top_up_choose_payment_method_"),
                        InlineKeyboardButton(text="Удалить eSIM", callback_data=f"delete_esim_{iccid}"),
                    ).adjust(1).as_markup()
                    try:
                        await Config.BOT.send_message(chat_id=user[0],
                                                      text=f"🪫 У вас заканчивается пакет интернета"
                                                           f" на eSIM “`{esim_info["country"]} - {iccid[-4:]}`”"
                                                           " (осталось меньше 1 ГБ)."
                                                           "\n\n👇 Нажмите соответствующую кнопку ниже,"
                                                           " чтобы продлить свой тариф или"
                                                           " *безвозвратно удалить* ненужную eSIM (оставшийся тариф"
                                                           " будет работать, но по"
                                                           " удаленной eSIM не будут приходить"
                                                           " уведомления, а так же она не будет отображаться"
                                                           " в списке ваших eSIM по команде /get\_my\_esims).",
                                                      reply_markup=kb)
                    except Exception as e:
                        print(f"Произошла ошибка при отправке сообщения пользователю с chat_id={user[0]} - {e}")


asyncio.run(send_remaining_info())
