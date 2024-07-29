import asyncio

from aiogram import types
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bnesim import BnesimApi
from config import Config
from db.db_get_my_esims import db_get_cli
from db.db_top_up_data import db_update_top_up_data_iccid_and_country, db_get_top_up_data_country, db_update_top_up_data_volume


async def get_my_esims_service(message: Message):
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


async def get_esim_info_service(callback: CallbackQuery):
    bnesim = BnesimApi()
    iccid = callback.data.split("_")[-1]
    esim_info = bnesim.get_esim_info(iccid)

    db_update_top_up_data_iccid_and_country(callback.message.chat.id, iccid, esim_info["country"])

    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="Продлить", callback_data="top_up_choose_payment_method")
    ).as_markup()
    await Config.BOT.send_photo(
        chat_id=callback.message.chat.id,
        photo=BufferedInputFile(esim_info["qr_code_image"], "png_qr_code.png"),
        caption=f"🛜 *Оставшийся интернет-трафик* - `{esim_info['remaining_data']} GB`",
        reply_markup=kb
    )


async def top_up_choose_payment_method_service(callback: CallbackQuery):
    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="💳 Российская карта", callback_data="top_up_choose_plan_russian"),
        InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data="top_up_choose_plan_star")
    ).adjust(1).as_markup()

    if callback.data.split("_")[-1] == "back":
        await callback.message.edit_text("*Выберите способ оплаты.*", reply_markup=kb)
    else:
        await callback.message.answer("*Выберите способ оплаты.*", reply_markup=kb)


async def top_up_choose_plan_service(callback: CallbackQuery, prices, currency):
    kb = InlineKeyboardBuilder().add(
        *[InlineKeyboardButton(text=f"{gb} ГБ - {price} {currency}",
                               callback_data=f"top_up_pay_{currency.lower()}_{gb}") for gb, price in prices.items()],
        InlineKeyboardButton(text="⏪ Назад", callback_data="top_up_choose_payment_method_back")
    ).adjust(2, 2, 1).as_markup()

    await callback.message.edit_text(text="*Выберите интересующий вас объем интернет-трафика.*", reply_markup=kb)


async def top_up_choose_plan_russian_service(callback: CallbackQuery):
    prices = {
        3: Config.PRICE_3_GB_RUB,
        5: Config.PRICE_5_GB_RUB,
        10: Config.PRICE_10_GB_RUB,
        20: Config.PRICE_20_GB_RUB
    }
    await top_up_choose_plan_service(callback, prices, 'RUB')


async def top_up_choose_plan_star_service(callback: CallbackQuery):
    prices = {
        3: Config.PRICE_3_GB_STAR,
        5: Config.PRICE_5_GB_STAR,
        10: Config.PRICE_10_GB_STAR,
        20: Config.PRICE_20_GB_STAR
    }
    await top_up_choose_plan_service(callback, prices, 'STARS')


async def top_up_pay_service(callback: CallbackQuery, prices, currency):
    gb_amount = int(callback.data.split("_")[-1])
    db_update_top_up_data_volume(callback.message.chat.id, gb_amount)
    amount = prices[gb_amount]
    country = db_get_top_up_data_country(callback.message.chat.id)

    invoice_params = {
        'chat_id': callback.from_user.id,
        'title': f"{country.capitalize()} - {gb_amount}GB",
        'description': f"Вы приобретаете указанный ранее пакет интернета в выбранной вами стране с помощью {currency}.",
        'provider_token': Config.YUKASSA_LIVE_TOKEN if currency == 'RUB' else '',
        'currency': currency.lower() if currency == 'RUB' else 'XTR',
        'photo_url': "https://i.imgur.com/MOnD80s.jpeg",
        'photo_width': 416,
        'photo_height': 234,
        'is_flexible': False,
        'prices': [types.LabeledPrice(label=f"Оплата esim с помощью {currency}",
                                      amount=amount * 100 if currency == 'RUB' else amount)],
        'payload': "test-invoice-payload"
    }

    if currency == 'RUB':
        invoice_params.update({
            'need_email': True,
            'send_email_to_provider': True,
            'provider_data': f"{{'receipt': {{'customer': {{'email': 'hipstakrippo@gmail.com'}},"
                             f"'items': [{{'description': '', 'amount': {{'value': '{amount}',"
                             f" 'currency': 'RUB'}}, 'vat_code': 1, 'quantity': 1}}]}}}}"
        })

    await Config.BOT.send_invoice(**invoice_params)


async def top_up_pay_russian_card_service(callback: CallbackQuery):
    prices = {
        3: Config.PRICE_3_GB_RUB,
        5: Config.PRICE_5_GB_RUB,
        10: Config.PRICE_10_GB_RUB,
        20: Config.PRICE_20_GB_RUB
    }
    await top_up_pay_service(callback, prices, 'RUB')


async def top_up_pay_star_service(callback: CallbackQuery):
    prices = {
        3: Config.PRICE_3_GB_STAR,
        5: Config.PRICE_5_GB_STAR,
        10: Config.PRICE_10_GB_STAR,
        20: Config.PRICE_20_GB_STAR
    }
    await top_up_pay_service(callback, prices, 'STARS')
