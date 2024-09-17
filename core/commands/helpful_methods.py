import random

from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from db.countries.db_pay_pic_link import db_get_pay_pic_link
from db.db_bnesim_products import db_get_price_data
from db.users.db_data import db_get_data_country, db_update_data_volume
from db.users.db_payments import db_save_invoice_user
from db.users.db_top_up_data import db_get_top_up_data_country, db_update_top_up_data_volume, \
    db_update_top_up_flag_true, db_update_top_up_flag_false
from robokassa_api import generate_payment_link


def get_username(message):
    if message.from_user.username is None:
        username = message.from_user.first_name
    else:
        username = '@' + message.from_user.username
    return username


async def choose_country(msg: Message | CallbackQuery):
    buttons = [
        InlineKeyboardButton(text="🇹🇷Турция", callback_data="choose_payment_method_turkey"),
        InlineKeyboardButton(text="🇹🇭Тайланд", callback_data="choose_payment_method_thailand"),
        InlineKeyboardButton(text="🇬🇪Грузия", callback_data="choose_payment_method_georgia"),
        InlineKeyboardButton(text="🇪🇬Египет", callback_data="choose_payment_method_egypt"),
        InlineKeyboardButton(text="🇮🇹Италия", callback_data="choose_payment_method_italy"),
        InlineKeyboardButton(text="🇪🇺Европа", callback_data="choose_payment_method_europe"),
    ]
    kb = build_keyboard(buttons, (2,))

    message_text = (
        "🚨 *Перед тем, как выбрать страну,"
        " обязательно удостоверьтесь в том, что ваш смартфон поддерживает технологию eSIM*."
        "\nВы можете проверить это, следуя шагам из"
        " [инструкции](https://telegra.ph/Kak-ponyat-chto-u-menya-est-vozmozhnost-podklyuchit-eSIM-07-27)."
        "\n\n👇*Выберите одну из доступных стран (список стран со временем будет активно пополняться).*"
    )
    if isinstance(msg, CallbackQuery):
        await msg.message.answer(text=message_text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await msg.answer(text=message_text, reply_markup=kb, disable_web_page_preview=True)


def build_keyboard(buttons, adjust_params):
    kb = InlineKeyboardBuilder()
    for button in buttons:
        kb.add(button)
    return kb.adjust(*adjust_params).as_markup()


def get_plan_prices(currency, chat_id, is_top_up=False):
    # Определяем страну в зависимости от флага is_top_up
    country = db_get_top_up_data_country(chat_id) if is_top_up else db_get_data_country(chat_id)

    # Получаем данные о ценах
    price_data = db_get_price_data(country)

    # Определяем множитель в зависимости от валюты
    multiplier = (
        Config.EURO_EXCHANGE_RATE if currency == 'RUB'
        else Config.EURO_EXCHANGE_RATE / 1.3
    )

    # Рассчитываем цены для каждого плана
    prices = {}
    for plan in [3, 5, 10, 20]:
        price = float(price_data[plan]["price"])
        percentage_of_profit = float(price_data[plan]["percentage_of_profit"])
        prices[plan] = int(price * percentage_of_profit * multiplier)

    return prices


async def pay_service(callback: CallbackQuery, currency, is_top_up=False):
    chat_id = callback.message.chat.id
    gb_amount = int(callback.data.split("_")[-1])
    if is_top_up:
        db_update_top_up_flag_true(chat_id)
        country = db_get_top_up_data_country(chat_id)
        db_update_top_up_data_volume(chat_id, gb_amount)
    else:
        db_update_top_up_flag_false(chat_id)
        country = db_get_data_country(chat_id)
        db_update_data_volume(chat_id, gb_amount)
    prices = get_plan_prices(currency, chat_id, is_top_up)
    amount = prices[gb_amount]
    photo_url = db_get_pay_pic_link(country)
    if currency == "XTR":
        invoice_params = {
            'chat_id': callback.from_user.id,
            'title': f"Счет “{country.capitalize()} - {gb_amount}GB”",
            'description': f"Вы выбрали тариф “{country.capitalize()} - {gb_amount}”."
                           " ⚠️ Учтите: активным для оплаты считается счет, выставленный последним в диалоге.",
            'provider_token': Config.YOKASSA_TEST_TOKEN if currency == 'RUB' else '',
            'currency': 'rub' if currency == 'RUB' else 'XTR',
            'photo_url': photo_url if photo_url else '',
            'photo_width': 485,
            'photo_height': 300,
            'is_flexible': False,
            'prices': [types.LabeledPrice(label=f"eSIM payment using {currency}",
                                          amount=amount * 100 if currency == 'RUB' else amount)],
            'payload': "test-invoice-payload"
        }
        await Config.BOT.send_invoice(**invoice_params)
    else:
        digits = random.randint(3, 10)
        invoice_id = random.randint(10 ** (digits - 1), (10 ** digits) - 1)
        db_save_invoice_user(invoice_id, chat_id, get_username(callback.message))
        payment_link = generate_payment_link(Config.MERCHANT_LOGIN, Config.TEST_PASSWORD1, amount, invoice_id,
                                             f"{country} - {amount}", 1)
        kb = InlineKeyboardBuilder().add(
            InlineKeyboardButton(text="Оплатить", url=payment_link)
        ).as_markup()
        await Config.BOT.send_photo(chat_id=chat_id,
                                    photo=photo_url,
                                    caption="Нажмите кнопку ниже для оплаты:",
                                    reply_markup=kb)
