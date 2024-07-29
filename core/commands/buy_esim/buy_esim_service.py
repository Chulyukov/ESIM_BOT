import asyncio
import json

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bnesim import BnesimApi
from config import Config
from core.helpful_methods import get_username
from db.db_buy_esim import db_get_product_id, db_update_cli
from db.db_data import db_update_data_country, db_update_data_volume, db_get_data_country, db_get_all_data, \
    db_clean_data
from db.db_get_my_esims import db_get_cli
from db.db_top_up_data import db_get_all_top_up_data, db_clean_top_up_data


def build_keyboard(buttons, adjust_params):
    kb = InlineKeyboardBuilder()
    for button in buttons:
        kb.add(button)
    return kb.adjust(*adjust_params).as_markup()


def get_plan_prices(currency):
    if currency == 'RUB':
        return {
            3: Config.PRICE_3_GB_RUB,
            5: Config.PRICE_5_GB_RUB,
            10: Config.PRICE_10_GB_RUB,
            20: Config.PRICE_20_GB_RUB
        }
    return {
        3: Config.PRICE_3_GB_STAR,
        5: Config.PRICE_5_GB_STAR,
        10: Config.PRICE_10_GB_STAR,
        20: Config.PRICE_20_GB_STAR
    }


async def buy_esim_service(msg: Message | CallbackQuery):
    buttons = [
        InlineKeyboardButton(text="🇹🇷Турция", callback_data="choose_payment_method_turkey"),
        InlineKeyboardButton(text="🇦🇪ОАЭ", callback_data="choose_payment_method_uae"),
        InlineKeyboardButton(text="🇹🇭Тайланд", callback_data="choose_payment_method_thailand"),
        InlineKeyboardButton(text="🇬🇪Грузия", callback_data="choose_payment_method_georgia"),
        InlineKeyboardButton(text="🇪🇬Египет", callback_data="choose_payment_method_egypt")
    ]
    kb = build_keyboard(buttons, (1, 2))

    message_text = (
        "Перед тем, как выбрать страну, *обязательно проверьте возможность установки esim на ваш смартфон*."
        "\nСписок девайсов, поддерживающих данную функцию, вы найдете по ссылке: *ссылка на Telegraph*"
        "\n\n👇*Выберите одну из доступных стран.*"
    )

    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(text=message_text, reply_markup=kb, disable_web_page_preview=True)
    elif isinstance(msg, Message):
        await msg.answer(text=message_text, reply_markup=kb, disable_web_page_preview=True)


async def choose_payment_method_service(callback: CallbackQuery):
    db_update_data_country(callback.message.chat.id, callback.data.split("_")[-1])
    buttons = [
        InlineKeyboardButton(text="💳 Российская карта", callback_data="choose_plan_russian_card"),
        InlineKeyboardButton(text="⭐️ Telegram Stars", callback_data="choose_plan_star"),
        InlineKeyboardButton(text="⏪ Назад", callback_data="buy_esim")
    ]
    kb = build_keyboard(buttons, (1,))
    await callback.message.edit_text("*Выберите способ оплаты.*", reply_markup=kb)


async def choose_plan_service(callback: CallbackQuery, currency):
    prices = get_plan_prices(currency)
    buttons = [
        InlineKeyboardButton(text=f"{gb} ГБ - {price} {currency}", callback_data=f"pay_{currency.lower()}_{gb}")
        for gb, price in prices.items()
    ]
    buttons.append(InlineKeyboardButton(text="⏪ Назад", callback_data="choose_payment_method_"))
    kb = build_keyboard(buttons, (2, 2, 1))
    await callback.message.edit_text(text="*Выберите интересующий вас объем интернет-трафика.*", reply_markup=kb)


async def choose_plan_russian_service(callback: CallbackQuery):
    await choose_plan_service(callback, 'RUB')


async def choose_plan_star_service(callback: CallbackQuery):
    await choose_plan_service(callback, 'STARS')


async def pay_service(callback: CallbackQuery, currency):
    country = db_get_data_country(callback.message.chat.id)
    gb_amount = int(callback.data.split("_")[-1])
    db_update_data_volume(callback.message.chat.id, gb_amount)
    prices = get_plan_prices(currency)
    amount = prices[gb_amount]
    title = f"{country.capitalize()} - {gb_amount}GB"
    description = f"Вы приобретаете указанный ранее пакет интернета в выбранной вами стране с помощью {currency}."

    invoice_params = {
        'chat_id': callback.from_user.id,
        'title': title,
        'description': description,
        'provider_token': Config.YUKASSA_LIVE_TOKEN if currency == 'RUB' else '',
        'currency': 'rub' if currency == 'RUB' else 'XTR',
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
            'provider_data': json.dumps({
                'receipt': {
                    'customer': {'email': 'hipstakrippo@gmail.com'},
                    'items': [{
                        'description': '',
                        'amount': {'value': str(amount), 'currency': 'RUB'},
                        'vat_code': 1,
                        'quantity': 1
                    }]
                }
            })
        })
    await Config.BOT.send_invoice(**invoice_params)


async def pay_russian_card_service(callback: CallbackQuery):
    await pay_service(callback, 'RUB')


async def pay_star_service(callback: CallbackQuery):
    await pay_service(callback, 'STARS')


async def calculate_successfull_payment(message: Message):
    chat_id = message.chat.id
    bnesim = BnesimApi()
    cli = db_get_cli(chat_id)
    top_up_data = db_get_all_top_up_data(chat_id)
    downloading_message = await message.answer("🚀 Подождите, обрабатываю данные платежа...")

    if cli is None:
        data = json.loads(db_get_all_data(message.chat.id))
        cli = bnesim.activate_user(f"{get_username(message)}_{chat_id}")
        product_id = db_get_product_id(data[0].capitalize(), data[1])
        db_update_cli(chat_id, cli)
        qr_code = bnesim.activate_esim(cli, product_id)
        while cli is None and qr_code is None:
            await asyncio.sleep(1)
        db_clean_data(chat_id)
        await Config.BOT.delete_message(chat_id=message.chat.id, message_id=downloading_message.message_id)
        await Config.BOT.send_photo(chat_id=message.chat.id, photo=BufferedInputFile(qr_code, "png_qr_code.png"),
                                    caption="Успешное приобретение esim!")
    else:
        if len(top_up_data) > 30:
            top_up_data = json.loads(db_get_all_top_up_data(message.chat.id))
            product_id = db_get_product_id(top_up_data[1], top_up_data[2])
            iccids_map = bnesim.get_iccids_of_user(cli)
            if top_up_data[0] in iccids_map["iccids"]:
                api_answer = bnesim.top_up_existing_esim(cli, top_up_data[0], product_id)
                db_clean_top_up_data(chat_id)
                while api_answer is None:
                    await asyncio.sleep(1)
                await Config.BOT.delete_message(chat_id=message.chat.id, message_id=downloading_message.message_id)
                await message.answer("Успешное продление esim!")
        else:
            data = json.loads(db_get_all_data(message.chat.id))
            product_id = db_get_product_id(data[0], data[1])
            qr_code = bnesim.activate_esim(cli, product_id)
            while qr_code is None:
                await asyncio.sleep(1)
            db_clean_data(chat_id)
            await Config.BOT.delete_message(chat_id=message.chat.id, message_id=downloading_message.message_id)
            await Config.BOT.send_photo(chat_id=message.chat.id, photo=BufferedInputFile(qr_code, "png_qr_code.png"),
                                        caption="Спасибо за приобретение новой esim!")

