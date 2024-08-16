import asyncio

from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, BufferedInputFile

from bnesim_api import BnesimApi
from config import Config
from core.helpful_methods import get_username, get_plan_prices, build_keyboard, pay_service, buy_esim_service
from db.db_bnesim_products import db_get_product_id
from db.users.db_users_cli import db_get_cli, db_update_cli
from db.users.db_users_data import db_update_data_country, db_get_all_data, db_clean_data
from db.users.db_users_top_up_data import db_get_all_top_up_data, db_clean_top_up_data, db_get_top_up_flag

router = Router()


@router.callback_query(F.data == "buy_esim")
@router.message(Command("buy_esim"))
async def buy_esim(message: Message | CallbackQuery):
    await buy_esim_service(message)


@router.callback_query(F.data.startswith("choose_payment_method_"))
async def choose_payment_method(callback: CallbackQuery):
    country = callback.data.split("_")[-1]
    db_update_data_country(callback.message.chat.id, callback.data.split("_")[-1])
    buttons = [
        InlineKeyboardButton(text="💳 Российская карта", callback_data=f"choose_plan_rub_{country}"),
        InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data=f"choose_plan_star_{country}"),
        InlineKeyboardButton(text="⏪ Назад", callback_data="buy_esim")
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
    buttons.append(InlineKeyboardButton(text="⏪ Назад", callback_data="buy_esim"))
    kb = build_keyboard(buttons, (2, 2, 1))
    await callback.message.edit_text(text="*Выберите интересующий вас пакет интернета.*", reply_markup=kb)


@router.callback_query(F.data.startswith("choose_plan_star_"))
async def choose_plan_star_card(callback: CallbackQuery):
    country = callback.data.split("_")[-1]
    db_update_data_country(callback.message.chat.id, country)
    prices = get_plan_prices("XRT", callback.message.chat.id)
    buttons = [
        InlineKeyboardButton(text=f"{gb} ГБ - {price} STARS", callback_data=f"pay_stars_{gb}")
        for gb, price in prices.items()
    ]
    buttons.append(InlineKeyboardButton(text="⏪ Назад", callback_data="buy_esim"))
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
        data = db_get_all_data(message.chat.id)
        top_up_data = db_get_all_top_up_data(chat_id)
        downloading_message = await message.answer("*🚀 Подождите, обрабатываю данные платежа...*")
        iccids_list = bnesim.get_iccids_of_user(cli)
        top_up_flag = db_get_top_up_flag(chat_id)

        if cli is None:
            cli = bnesim.activate_user(f"{get_username(message)}_{chat_id}")
            product_id = db_get_product_id(data[0], data[1])
            db_update_cli(chat_id, cli)
            active_esim = bnesim.activate_esim(cli, product_id)
            while cli is None and active_esim[1] is None:
                await asyncio.sleep(1)
            db_clean_data(chat_id)
            await Config.BOT.delete_message(chat_id=message.chat.id, message_id=downloading_message.message_id)
            await Config.BOT.send_photo(chat_id=message.chat.id, photo=BufferedInputFile(active_esim[1],
                                                                                         "png_qr_code.png"),
                                        caption="*🎊 Успешное приобретение вашей первой eSIM!*"
                                                "\n\n☎️ *Название вашей eSIM:*"
                                                f" `{data[0].capitalize()} - {active_esim[0][-4:]}`"
                                                "\n\n*Инструкция по установке:* Telegraph"
                                                "\n\nТакже вы можете посмотреть подробную информацию о ваших eSIM"
                                                " с помощью команды /get\_my\_esims")
        elif (top_up_data is not None and len(top_up_data) == 3 and "iccid" in top_up_data
              and top_up_data["iccid"] in [item for item in iccids_list["iccids"]]
              and top_up_flag == 1):
            product_id = db_get_product_id(top_up_data["country"], top_up_data["volume"])
            iccids_map = bnesim.get_iccids_of_user(cli)
            if top_up_data["iccid"] in iccids_map["iccids"]:
                api_answer = bnesim.top_up_existing_esim(cli, top_up_data["iccid"], product_id)
                db_clean_top_up_data(chat_id)
                while api_answer is None:
                    await asyncio.sleep(1)
                await Config.BOT.delete_message(chat_id=message.chat.id, message_id=downloading_message.message_id)
                await message.answer("*🎊 Успешное продление eSIM!*"
                                     f"\n\n*📛 Название вашей eSIM:*"
                                     f" `{top_up_data["country"].capitalize()} - {top_up_data["iccid"][-4:]}`"
                                     f"\n\nВы можете посмотреть инструкцию по установке и"
                                     f" подробную информацию о ваших eSIM с помощью команды /get\_my\_esims")
        else:
            product_id = db_get_product_id(data[0], data[1])
            active_esim = bnesim.activate_esim(cli, product_id)
            while active_esim[1] is None:
                await asyncio.sleep(1)
            db_clean_data(chat_id)
            await Config.BOT.delete_message(chat_id=message.chat.id, message_id=downloading_message.message_id)
            await Config.BOT.send_photo(chat_id=message.chat.id, photo=BufferedInputFile(active_esim[1],
                                                                                         "png_qr_code.png"),
                                        caption="🎊 Спасибо за приобретение новой eSIM!"
                                                "\n\n📛 *Название вашей eSIM:*"
                                                f" `{data[0].capitalize()} - {active_esim[0][-4:]}` "
                                                "\n\nВы можете посмотреть инструкцию по установке и"
                                                " подробную информацию о ваших eSIM с помощью команды /get\_my\_esims")
