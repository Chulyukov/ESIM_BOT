import asyncio

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bnesim_api import BnesimApi
from config import Config
from db.users.db_cli import db_get_all_cli

bnesim_api = BnesimApi()
users_list = db_get_all_cli()


async def send_remaining_info():
    for user in users_list:
        iccids_dict = bnesim_api.get_iccids_of_user(user[1])
        if iccids_dict["length"] > 0:
            for iccid in iccids_dict["iccids"]:
                esim_info = bnesim_api.get_esim_info(iccid)
                if esim_info is not None and esim_info['remaining_data'] <= 0.5:
                    kb = InlineKeyboardBuilder().add(
                        InlineKeyboardButton(text="Продлить", callback_data="top_up_choose_payment_method_")
                    ).as_markup()
                    try:
                        await Config.BOT.send_message(chat_id=user[0],
                                                      text=f"🪫 У вас заканчивается пакет интернета"
                                                           f" на eSIM “`{esim_info["country"]} - {iccid[-4:]}`”"
                                                           " (осталось меньше 0,5 ГБ)."
                                                           "\n\n👇 Нажмите кнопку ниже, чтобы продлить свой тариф.",
                                                      reply_markup=kb)
                    except Exception as e:
                        print(f"Произошла ошибка при отправке сообщения пользователю с chat_id={user[0]} - {e}")


asyncio.run(send_remaining_info())
