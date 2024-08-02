import asyncio

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bnesim_api import BnesimApi
from config import Config
from core.helpful_methods import get_plan_prices, pay_service
from db.db_get_my_esims import db_get_cli
from db.db_top_up_data import db_update_top_up_data_iccid_and_country

router = Router()


@router.message(Command("get_my_esims"))
async def get_my_esims(message: Message):
    bnesim = BnesimApi()
    cli = db_get_cli(message.chat.id)

    downloading_message = await message.answer("🚀 Подождите, загружаю данные...")
    iccids_map = bnesim.get_iccids_of_user(cli)

    while iccids_map is None:
        await asyncio.sleep(1)

    await Config.BOT.delete_message(chat_id=message.chat.id, message_id=downloading_message.message_id)

    if iccids_map["length"] == 0:
        kb = InlineKeyboardBuilder().add(
            InlineKeyboardButton(text="Приобрести esim", callback_data="buy_esim")
        ).as_markup()
        await message.answer(
            text="*💔 Мы не нашли у вас ни одной esim, но вы можете приобрести их, нажав кнопку ниже.*",
            reply_markup=kb
        )
    else:
        kb = InlineKeyboardBuilder()
        for iccid in iccids_map.get("iccids", []):
            kb.add(InlineKeyboardButton(text=f"***{iccid[-4:]}", callback_data=f"get_esim_info_{iccid}"))
        kb = kb.adjust(1).as_markup()
        await message.answer(
            text="Выберите интересующую вас esim, чтобы посмотреть детальную информацию по ней.",
            reply_markup=kb
        )


@router.callback_query(F.data.startswith("get_esim_info_"))
async def get_esim_info(callback: CallbackQuery):
    bnesim = BnesimApi()
    iccid = callback.data.split("_")[-1]
    esim_info = bnesim.get_esim_info(iccid)

    db_update_top_up_data_iccid_and_country(callback.message.chat.id, iccid, esim_info["country"])

    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="Продлить", callback_data="top_up_choose_plan_rub")
    ).as_markup()
    await Config.BOT.send_photo(
        chat_id=callback.message.chat.id,
        photo=BufferedInputFile(esim_info["qr_code_image"], "png_qr_code.png"),
        caption=f"🛜 *Оставшийся интернет-трафик* - `{esim_info['remaining_data']} GB`",
        reply_markup=kb
    )


# @router.callback_query(F.data.startswith("top_up_choose_payment_method"))
# async def top_up_choose_payment_method(callback: CallbackQuery):
#     kb = InlineKeyboardBuilder().add(
#         InlineKeyboardButton(text="💳 Российская карта", callback_data="top_up_choose_plan_russian"),
#         InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data="top_up_choose_plan_star")
#     ).adjust(1).as_markup()
#
#     if callback.data.split("_")[-1] == "back":
#         await callback.message.edit_text("*Выберите способ оплаты.*", reply_markup=kb)
#     else:
#         await callback.message.answer("*Выберите способ оплаты.*", reply_markup=kb)


@router.callback_query(F.data == "top_up_choose_plan_rub")
async def top_up_choose_plan_russian(callback: CallbackQuery):
    prices = get_plan_prices("RUB", callback.message.chat.id, True)
    kb = InlineKeyboardBuilder().add(
        *[InlineKeyboardButton(text=f"{gb} ГБ - {price} RUB",
                               callback_data=f"top_up_pay_rub_{gb}") for gb, price in prices.items()],
    ).adjust(2, 2, 1).as_markup()

    await callback.message.answer(text="*Выберите интересующий вас пакет интернета.*", reply_markup=kb)


# @router.callback_query(F.data == "top_up_choose_plan_star")
# async def top_up_choose_plan_star(callback: CallbackQuery):
#         prices = {
#         3: Config.PRICE_3_GB_STAR,
#         5: Config.PRICE_5_GB_STAR,
#         10: Config.PRICE_10_GB_STAR,
#         20: Config.PRICE_20_GB_STAR
#     }
#     kb = InlineKeyboardBuilder().add(
#         *[InlineKeyboardButton(text=f"{gb} ГБ - {price} 'STARS'",
#                                callback_data=f"top_up_pay_stars_{gb}") for gb, price in prices.items()],
#         InlineKeyboardButton(text="⏪ Назад", callback_data="top_up_choose_payment_method_back")
#     ).adjust(2, 2, 1).as_markup()
#
#     await callback.message.answer(text="*Выберите интересующий вас объем интернет-трафика.*", reply_markup=kb)


@router.callback_query(F.data.startswith("top_up_pay_rub_"))
async def top_up_pay_rub(callback: CallbackQuery):
    await pay_service(callback, 'RUB', True)


# @router.callback_query(F.data.startswith("top_up_pay_stars_"))
# async def top_up_pay_star(callback: CallbackQuery):
#     prices = get_plan_prices("STARS", callback.message.chat.id, True)
#     await top_up_pay_service(callback, prices, 'STARS')