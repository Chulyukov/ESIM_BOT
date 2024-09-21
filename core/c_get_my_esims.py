import asyncio

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bnesim_api import BnesimApi
from config import Config
from core.helpful_methods import get_plan_prices, prepare_payment_order
from db.users.db_cli import db_get_cli
from db.users.db_hidden_esims import db_get_hidden_esims
from db.users.db_top_up_data import db_update_top_up_data_iccid_and_country

router = Router()


@router.message(Command("get_my_esims"))
async def get_my_esims(message: Message):
    chat_id = message.chat.id
    bnesim = BnesimApi()
    cli = db_get_cli(chat_id)

    downloading_message = await message.answer("*🚀 Подождите, загружаю данные...*")
    iccids_map = bnesim.get_iccids_of_user(cli)

    while iccids_map is None:
        await asyncio.sleep(1)

    if iccids_map["length"] == 0:
        kb = InlineKeyboardBuilder().add(
            InlineKeyboardButton(text="Приобрести eSIM", callback_data="buy_esim")
        ).as_markup()
        await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
        await message.answer(
            text="*💔 Мы не нашли у вас ни одной eSIM, но вы можете приобрести их, нажав кнопку ниже.*",
            reply_markup=kb
        )
    else:
        kb = InlineKeyboardBuilder()
        hidden_esims = db_get_hidden_esims(chat_id)
        for iccid in iccids_map.get("iccids", []):
            esim_info = bnesim.get_esim_info(iccid)
            if esim_info is not None:
                if hidden_esims is not None and iccid in hidden_esims:
                    continue
                kb.add(InlineKeyboardButton(text=f"{esim_info["country"]} - {iccid[-4:]}",
                                            callback_data=f"get_esim_info_{iccid}"))
        kb = kb.adjust(1).as_markup()
        await Config.BOT.delete_message(chat_id=chat_id, message_id=downloading_message.message_id)
        await message.answer(
            text="*👇 Выберите одну из ваших eSIM,"
                 " чтобы узнать подробную информацию о ней или продлить пакет интернета.*",
            reply_markup=kb
        )


@router.callback_query(F.data.startswith("get_esim_info_"))
async def get_esim_info(callback: CallbackQuery):
    bnesim = BnesimApi()
    iccid = callback.data.split("_")[-1]
    esim_info = bnesim.get_esim_info(iccid)

    db_update_top_up_data_iccid_and_country(callback.message.chat.id, iccid, esim_info["country"])

    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="Продлить", callback_data="top_up_choose_payment_method_")
    ).as_markup()
    await Config.BOT.send_photo(
        chat_id=callback.message.chat.id,
        photo=BufferedInputFile(esim_info["qr_code_image"], "png_qr_code.png"),
        caption=f"*📛 Название eSIM:* `{esim_info['country'].capitalize()} - {iccid[-4:]}`"
                f"\n*🛜 Оставшийся интернет-трафик:* `{esim_info['remaining_data']} GB`"
                f"\n*🔗 Ссылка для прямой установки на IOS:* `{esim_info['ios_link']}`"
                "\n\n*📖 Инструкция по установке:*"
                " [iPhone](https://telegra.ph/Kak-podklyuchit-eSIM-na-iPhone-07-27)"
                " | [Android](https://telegra.ph/Kak-podklyuchit-eSIM-na-Android-08-18)"
                " | [Samsung](https://telegra.ph/Kak-podklyuchit-eSIM-na-Samsung-08-18)"
                " | [Huawei](https://telegra.ph/Kak-podklyuchit-eSIM-na-Huawei-08-18)"
                " | [Google Pixel](https://telegra.ph/Kak-podklyuchit-eSIM-na-Pixel-08-24)"
                "\n\n🏝️ Если во время установки у вас возникли какие-либо сложности,"
                f" обратитесь в службу заботы клиента eSIM Unity {Config.SUPPORT_SIMPLE_LINK}"
                f"\n\n👇 Также вы можете расширить интернет-пакет данной eSIM, нажав кнопку ниже.",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("top_up_choose_payment_method_"))
async def top_up_choose_payment_method(callback: CallbackQuery):
    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="💳 Российская карта", callback_data="top_up_choose_plan_rub"),
        InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data="top_up_choose_plan_star")
    ).adjust(1).as_markup()

    if callback.data.split("_")[-1] == "back":
        await callback.message.edit_text("*👇 Выберите способ оплаты.*", reply_markup=kb)
    else:
        await callback.message.answer("*👇 Выберите способ оплаты.*", reply_markup=kb)


@router.callback_query(F.data == "top_up_choose_plan_rub")
async def top_up_choose_plan_russian(callback: CallbackQuery):
    prices = get_plan_prices("RUB", callback.message.chat.id, True)
    kb = (InlineKeyboardBuilder().add(
        *[InlineKeyboardButton(text=f"{gb} ГБ - {price} RUB",
                               callback_data=f"top_up_pay_rub_{gb}") for gb, price in prices.items()],
        InlineKeyboardButton(text="⏪ Назад", callback_data="top_up_choose_payment_method_back")
    ).adjust(2, 2, 1).as_markup())

    await callback.message.edit_text(text="💳 Оплачивая российской картой, вы соглашаетесь с"
                                          " [условиями использования сервиса](https://telegra.ph/Kak-proishodit-oplata-v-bote-09-05)."
                                          "\n\n*Выберите интересующий вас пакет интернета.*",
                                     reply_markup=kb,
                                     disable_web_page_preview=True)


@router.callback_query(F.data == "top_up_choose_plan_star")
async def top_up_choose_plan_star(callback: CallbackQuery):
    prices = get_plan_prices("XRT", callback.message.chat.id, True)
    kb = InlineKeyboardBuilder().add(
        *[InlineKeyboardButton(text=f"{gb} ГБ - {price} STARS",
                               callback_data=f"top_up_pay_stars_{gb}") for gb, price in prices.items()],
        InlineKeyboardButton(text="⏪ Назад", callback_data="top_up_choose_payment_method_back")
    ).adjust(2, 2, 1).as_markup()

    await callback.message.edit_text(text="*👇 Выберите интересующий вас объем интернет-трафика.*", reply_markup=kb)


@router.callback_query(F.data.startswith("top_up_pay_rub_"))
async def top_up_pay_rub(callback: CallbackQuery):
    await prepare_payment_order(callback, 'RUB', True)


@router.callback_query(F.data.startswith("top_up_pay_stars_"))
async def top_up_pay_star(callback: CallbackQuery):
    await prepare_payment_order(callback, 'XTR', True)
