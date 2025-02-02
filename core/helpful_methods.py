import random
from datetime import datetime

from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from db.db_queries import (
    db_get_top_up_data_country, db_get_data_country, db_get_price_data,
    db_update_top_up_flag_true, db_update_top_up_data_volume,
    db_update_top_up_flag_false, db_update_data_volume, db_get_emoji,
    db_get_ru_name, db_get_pay_pic_link, db_save_invoice_user
)
from currency_rate import get_dollar_to_rub_rate
from monty_api import MontyApi
from robokassa_api import generate_payment_link


def get_username(message):
    """Получение имени пользователя."""
    return f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name


def build_keyboard(buttons, layout):
    """Создание клавиатуры с заданной раскладкой."""
    kb = InlineKeyboardBuilder()
    kb.add(*buttons)
    return kb.adjust(*layout).as_markup()


def get_bundle_price_list(country):
    """Получение цен для тарифов по стране."""
    multiplier = get_dollar_to_rub_rate()
    processed_bundle_data = {}

    monty = MontyApi()
    bundle_data = monty.get_bundle_data(country)

    for gb_amount in [3, 5, 10, 20]:
        bundle_price = 10000
        subscriber_price = ""
        bundle_code = ""
        for bundle in bundle_data:
            if ((f"{gb_amount}GB" in bundle["bundle_name"] or
                 f"{float(gb_amount) * 1024}MB" in bundle["bundle_name"]) and bundle_price > bundle["subscriber_price"]) and bundle["validity"] == 30:
                bundle_price = bundle["subscriber_price"]
                subscriber_price = bundle["subscriber_price"]
        if subscriber_price:
            processed_bundle_data[str(gb_amount)] = float(subscriber_price) * multiplier * 1.04 * 1.06 * 1.2 * 1.2 * 1.4

    return processed_bundle_data


def get_bundle_code(country, gb_amount):
    """Получение bundle_code по стране, количеству ГБ."""
    monty = MontyApi()
    bundle_data = monty.get_bundle_data(country)

    bundle_price = 10000
    bundle_code = ""
    for bundle in bundle_data:
        if ((f"{gb_amount}GB" in bundle["bundle_name"] or
             f"{float(gb_amount) * 1024}MB" in bundle["bundle_name"]) and bundle_price > bundle["subscriber_price"]) and bundle["validity"] == 30:
            bundle_price = bundle["subscriber_price"]
            bundle_code = bundle["bundle_code"]

    return bundle_code


async def prepare_payment_order(callback: CallbackQuery, currency, is_top_up=False):
    """Подготовка счета для оплаты."""
    chat_id = str(callback.message.chat.id)
    gb_amount = int(callback.data.split("_")[-1])
    country = db_get_top_up_data_country(chat_id) if is_top_up else db_get_data_country(chat_id)

    if is_top_up:
        db_update_top_up_flag_true(chat_id)
        db_update_top_up_data_volume(chat_id, gb_amount)
    else:
        db_update_top_up_flag_false(chat_id)
        db_update_data_volume(chat_id, gb_amount)

    emoji = db_get_emoji(country)
    ru_name = db_get_ru_name(country)
    prices = get_bundle_price_list(currency, chat_id, is_top_up)
    amount = prices[gb_amount]
    photo_url = db_get_pay_pic_link(country)

    if currency == "XTR":
        await send_invoice(callback, chat_id, emoji, ru_name, gb_amount, amount, photo_url, currency)
    else:
        await create_payment_link(callback, chat_id, emoji, ru_name, gb_amount, amount, photo_url, country)


async def send_invoice(callback, chat_id, emoji, ru_name, gb_amount, amount, photo_url, currency):
    """Отправка инвойса."""
    invoice_params = {
        'chat_id': chat_id,
        'title': f"Счет “{emoji}{ru_name.title()} - {gb_amount}GB”",
        'description': f"Вы выбрали тариф “{ru_name.title()} - {gb_amount}GB”.",
        'provider_token': Config.YOKASSA_TEST_TOKEN,
        'currency': currency,
        'prices': [types.LabeledPrice(label=f"eSIM payment using {currency}", amount=amount * 100)],
        'photo_url': photo_url or "",
    }
    await Config.BOT.send_invoice(**invoice_params)


async def create_payment_link(callback, chat_id, emoji, ru_name, gb_amount, amount, photo_url, country):
    """Создание и отправка ссылки на оплату."""
    invoice_id = random.randint(10 ** 4, 10 ** 5 - 1)
    username = get_username(callback.message)
    db_save_invoice_user(invoice_id, chat_id, username, datetime.now())
    payment_link = generate_payment_link(Config.MERCHANT_LOGIN, Config.PASSWORD1, amount, invoice_id, country, 0)

    kb = InlineKeyboardBuilder().add(
        InlineKeyboardButton(text="💳 Оплатить", url=payment_link)
    ).as_markup()
    caption = f"Вы выбрали тариф “{emoji}{ru_name.title()} - {gb_amount}GB”."

    await Config.BOT.send_message("1547142782", text=f"chat\_id: {chat_id}\n"
                                                     f"username: {username}\n"
                                                     f"gb\_amount: {gb_amount}\n"
                                                     f"amount: {str(amount)}\n"
                                                     f"country: {emoji}{country}\n"
                                                     f"payment\_link: {payment_link}\n")

    if photo_url:
        await Config.BOT.send_photo(chat_id, photo=photo_url, caption=caption, reply_markup=kb)
    else:
        await Config.BOT.send_message(chat_id, text=caption, reply_markup=kb)

# get_bundle_data("turkey")
