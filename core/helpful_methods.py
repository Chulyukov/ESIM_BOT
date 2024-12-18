import random
from datetime import datetime

from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from db.db_queries import (
    db_get_top_up_data_country, db_get_data_country, db_get_price_data,
    db_update_top_up_flag_true, db_update_top_up_data_volume,
    db_update_top_up_flag_false, db_update_data_volume, db_get_emoji_from_two_tables,
    db_get_ru_name_from_two_tables, db_get_pay_pic_link, db_save_invoice_user
)
from get_euro_rate import get_euro_to_rub_rate
from robokassa_api import generate_payment_link


def get_username(message):
    """Получение имени пользователя."""
    return f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name


async def choose_direction(msg: Message | CallbackQuery):
    """Отображение выбора направлений."""
    message_text = (
        "🚨 *Перед тем, как выбрать направление, "
        "удостоверьтесь, что ваш смартфон поддерживает eSIM.* "
        "[Инструкция](https://telegra.ph/Kak-ponyat-chto-u-menya-est-vozmozhnost-podklyuchit-eSIM-07-27).\n\n"
        "🔍 Вы можете в любое время ввести название страны, и бот покажет все подходящие варианты.\n\n"
        "🆘 Если у вас возникли сложности, свяжитесь со "
        "[службой заботы клиента](https://t.me/esim_unity_support).\n\n"
        "👇 *Выберите раздел.*"
    )
    kb = build_keyboard([
        InlineKeyboardButton(text="🔥 Популярные направления", callback_data="popular_directions"),
        InlineKeyboardButton(text="📍 Отдельные страны", callback_data="countries_0"),
        InlineKeyboardButton(text="🗺️ Регионы", callback_data="regions"),
        InlineKeyboardButton(text="🌎 Весь мир", callback_data="choose_plan_rub_global"),
    ], (1,))

    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(text=message_text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await msg.answer(text=message_text, reply_markup=kb, disable_web_page_preview=True)


def build_keyboard(buttons, layout):
    """Создание клавиатуры с заданной раскладкой."""
    kb = InlineKeyboardBuilder()
    kb.add(*buttons)
    return kb.adjust(*layout).as_markup()


def get_plan_prices(currency, chat_id, is_top_up=False):
    """Получение цен для тарифов."""
    country = db_get_top_up_data_country(chat_id) if is_top_up else db_get_data_country(chat_id)
    price_data = db_get_price_data(country)
    multiplier = get_euro_to_rub_rate() if currency == 'RUB' else get_euro_to_rub_rate() / 1.5
    return {
        plan: int(float(price_data[plan]["price"]) * multiplier * 1.04 * 1.06 * 1.2 * 1.2 * 1.3)
        for plan in [3, 5, 10, 20]
    }


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

    emoji = db_get_emoji_from_two_tables(country)
    ru_name = db_get_ru_name_from_two_tables(country)
    prices = get_plan_prices(currency, chat_id, is_top_up)
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