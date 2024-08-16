import asyncio

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bnesim_api import BnesimApi
from config import Config
from db.users.db_users_cli import db_get_all_cli

bnesim_api = BnesimApi()
result = db_get_all_cli()

logger.add('../logs/check_remaining_traffic.log', level='DEBUG', format='{time} | {level} | {name} | {message}')


async def send_remaining_info():
    for r in result:
        iccids_dict = bnesim_api.get_iccids_of_user(r[1])
        if iccids_dict["length"] > 0:
            for iccid in iccids_dict["iccids"]:
                esim_info = bnesim_api.get_esim_info(iccid)
                if esim_info['remaining_data'] <= 1.0:
                    kb = InlineKeyboardBuilder().add(
                        InlineKeyboardButton(text="Продлить", callback_data="top_up_choose_payment_method_")
                    ).as_markup()
                    try:
                        await Config.BOT.send_message(chat_id=r[0],
                                                      text=f"🪫 У вас заканчивается пакет интернета на eSIM “`{esim_info["country"]} - {iccid[-4:]}`”"
                                                           " (осталось меньше 1 ГБ)."
                                                           "\n\n👇 Нажмите кнопку ниже, чтобы продлить свой тариф.",
                                                      reply_markup=kb)
                    except Exception as e:
                        logger.info(f"Произошла ошибка при отправке сообщения пользователю с chat_id={r[0]} - {e}")


asyncio.run(send_remaining_info())
