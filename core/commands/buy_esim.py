from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton

from bnesim_api import BnesimApi
from config import Config
from helpful_methods import get_username, get_plan_prices, build_keyboard, pay_service, choose_country, \
    add_new_user_after_payment, add_new_esim_after_payment, prolong_esim_after_payment
from db.users.db_cli import db_get_cli
from db.users.db_data import db_update_data_country, db_get_all_data
from db.users.db_top_up_data import db_get_all_top_up_data, db_get_top_up_flag

router = Router()


@router.callback_query(F.data == "buy_esim")
@router.message(Command("buy_esim"))
async def buy_esim(message: Message | CallbackQuery):
    await choose_country(message)


@router.callback_query(F.data.startswith("choose_payment_method_"))
async def choose_payment_method(callback: CallbackQuery):
    country = callback.data.split("_")[-1]
    db_update_data_country(callback.message.chat.id, callback.data.split("_")[-1])
    buttons = [
        InlineKeyboardButton(text="💳 Российская карта", callback_data=f"choose_plan_rub_{country}"),
        InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data=f"choose_plan_star_{country}"),
        InlineKeyboardButton(text="⏪ К выбору страны", callback_data="buy_esim")
    ]
    kb = build_keyboard(buttons, (1,))
    await callback.message.edit_text("*Выберите способ оплаты.*", reply_markup=kb)


@router.callback_query(F.data.startswith("choose_plan_rub_"))
async def choose_plan_rub(callback: CallbackQuery):
    country = callback.data.split("_")[-1]
    db_update_data_country(callback.message.chat.id, country)
    prices = get_plan_prices("RUB", callback.message.chat.id)
    buttons = [
        InlineKeyboardButton(text=f"{gb} ГБ - {price} RUB", callback_data=f"pay_rub_{gb}")
        for gb, price in prices.items()
    ]
    buttons.append(InlineKeyboardButton(text="⏪ Назад", callback_data=f"choose_payment_method_{country}"))
    kb = build_keyboard(buttons, (2, 2, 1))
    await callback.message.edit_text(text="💳 Оплачивая российской картой, вы соглашаетесь с"
                                          " [условиями использования сервиса](https://telegra.ph/Kak-proishodit-oplata-v-bote-09-05)."
                                          "\n\n*Выберите интересующий вас пакет интернета.*",
                                     reply_markup=kb,
                                     disable_web_page_preview=True)


@router.callback_query(F.data.startswith("choose_plan_star_"))
async def choose_plan_star_card(callback: CallbackQuery):
    country = callback.data.split("_")[-1]
    db_update_data_country(callback.message.chat.id, country)
    prices = get_plan_prices("XRT", callback.message.chat.id)
    buttons = [
        InlineKeyboardButton(text=f"{gb} ГБ - {price} STARS", callback_data=f"pay_stars_{gb}")
        for gb, price in prices.items()
    ]
    buttons.append(InlineKeyboardButton(text="⏪ Назад", callback_data=f"choose_payment_method_{country}"))
    kb = build_keyboard(buttons, (2, 2, 1))
    await callback.message.edit_text(text="*Выберите интересующий вас пакет интернета.*", reply_markup=kb)


@router.callback_query(F.data.startswith("pay_rub_"))
async def pay_rub(callback: CallbackQuery):
    await pay_service(callback, "RUB")


@router.callback_query(F.data.startswith("pay_stars_"))
async def pay_star(callback: CallbackQuery):
    await pay_service(callback, "XTR")


@router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await Config.BOT.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    if message.successful_payment.total_amount in {111, 222, 333, 444}:
        await message.answer("🤗 Благодарим вас за поддержку нашего продукта!"
                             "\n💪 Мы ежедневно прилагаем усилия, чтобы сделать его еще лучше.")
    else:
        chat_id = message.chat.id
        bnesim = BnesimApi()
        cli = db_get_cli(chat_id)
        data = db_get_all_data(chat_id)
        top_up_data = db_get_all_top_up_data(chat_id)
        downloading_message = await message.answer("*🚀 Подождите, обрабатываю данные платежа...*")
        iccids_list = bnesim.get_iccids_of_user(cli)
        top_up_flag = db_get_top_up_flag(chat_id)

        if cli is None:
            cli = bnesim.activate_user(f"{get_username(message)}_{chat_id}")
            await add_new_user_after_payment(chat_id, data, cli, bnesim, downloading_message)
        elif (top_up_data is not None and len(top_up_data) == 3 and "iccid" in top_up_data
              and top_up_data["iccid"] in [item for item in iccids_list["iccids"]]
              and top_up_flag == 1):
            await prolong_esim_after_payment(chat_id, top_up_data, cli, bnesim, downloading_message)
        else:
            await add_new_esim_after_payment(chat_id, data, cli, bnesim, downloading_message)
