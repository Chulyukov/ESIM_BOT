import json

from aiogram import types
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from db.db_bnesim_products import db_get_price_data
from db.db_data import db_get_data_country, db_update_data_volume
from db.db_top_up_data import db_get_top_up_data_country, db_update_top_up_data_volume, \
    db_update_top_up_flag_true, db_update_top_up_flag_false


def get_username(message):
    if message.from_user.username is None:
        username = message.from_user.first_name
    else:
        username = '@' + message.from_user.username
    return username


async def buy_esim_service(msg):
    buttons = [
        InlineKeyboardButton(text="🇹🇷Турция", callback_data="choose_plan_rub_turkey"),
        InlineKeyboardButton(text="🇹🇭Тайланд", callback_data="choose_plan_rub_thailand"),
        InlineKeyboardButton(text="🇬🇪Грузия", callback_data="choose_plan_rub_georgia"),
        InlineKeyboardButton(text="🇪🇬Египет", callback_data="choose_plan_rub_egypt")
    ]
    kb = build_keyboard(buttons, (2,))

    message_text = (
        "🚨 Перед тем, как выбрать страну, *обязательно удостоверьтесь в том, что ваш смартфон поддерживает технологию eSIM*."
        "\nВы можете проверить это, следуя шагам из инструкции по ссылке: *ссылка на Telegraph*"
        "\n\n👇*Выберите одну из доступных стран (список стран со временем будет активно пополняться).*"
    )
    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(text=message_text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await msg.answer(text=message_text, reply_markup=kb, disable_web_page_preview=True)


def build_keyboard(buttons, adjust_params):
    kb = InlineKeyboardBuilder()
    for button in buttons:
        kb.add(button)
    return kb.adjust(*adjust_params).as_markup()


def get_plan_prices(currency, chat_id, is_top_up=False):
    if is_top_up:
        country = db_get_top_up_data_country(chat_id)
    else:
        country = db_get_data_country(chat_id)
    price_data = db_get_price_data(country)
    if currency == 'RUB':
        return {
            3: int(float(price_data[3]["price"]) * float(price_data[3]["percentage_of_profit"]) * 1.047 * Config.EURO_EXCHANGE_RATE),
            5: int(float(price_data[5]["price"]) * float(price_data[5]["percentage_of_profit"]) * 1.047 * Config.EURO_EXCHANGE_RATE),
            10: int(float(price_data[10]["price"]) * float(price_data[10]["percentage_of_profit"]) * 1.047 * Config.EURO_EXCHANGE_RATE),
            20: int(float(price_data[20]["price"]) * float(price_data[20]["percentage_of_profit"]) * 1.047 * Config.EURO_EXCHANGE_RATE),
        }
    return {
        3: int(float(price_data[3]["price"]) * float(price_data[3]["percentage_of_profit"]) * Config.EURO_EXCHANGE_RATE / 2.40),
        5: int(float(price_data[5]["price"]) * float(price_data[5]["percentage_of_profit"]) * Config.EURO_EXCHANGE_RATE / 2.40),
        10: int(float(price_data[10]["price"]) * float(price_data[10]["percentage_of_profit"]) * Config.EURO_EXCHANGE_RATE / 2.40),
        20: int(float(price_data[20]["price"]) * float(price_data[20]["percentage_of_profit"]) * Config.EURO_EXCHANGE_RATE / 2.40),
    }


async def pay_service(callback: CallbackQuery, currency, is_top_up=False):
    gb_amount = int(callback.data.split("_")[-1])
    if is_top_up:
        db_update_top_up_flag_true(callback.message.chat.id)
        country = db_get_top_up_data_country(callback.message.chat.id)
        db_update_top_up_data_volume(callback.message.chat.id, gb_amount)
    else:
        db_update_top_up_flag_false(callback.message.chat.id)
        country = db_get_data_country(callback.message.chat.id)
        db_update_data_volume(callback.message.chat.id, gb_amount)
    prices = get_plan_prices(currency, callback.message.chat.id, is_top_up)
    amount = prices[gb_amount]

    invoice_params = {
        'chat_id': callback.from_user.id,
        'title': f"{country.capitalize()} - {gb_amount}GB",
        'description': f"⚠️ Учтите: активным для оплаты считается счет, выставленный последним в диалоге.",
        'provider_token': Config.YOKASSA_TEST_TOKEN if currency == 'RUB' else '',
        'currency': 'rub' if currency == 'RUB' else 'XTR',
        # 'photo_url': "https://drive.google.com/file/d/1OYhHtsjpDgw40_l2nw47fQnav_oDDMAS/view?usp=sharing",
        # 'photo_width': 416,
        # 'photo_height': 416,
        'is_flexible': False,
        'prices': [types.LabeledPrice(label=f"eSIM payment using {currency}",
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
                        'description': 'eSIM payment',
                        'amount': {'value': str(amount), 'currency': 'RUB'},
                        'vat_code': 1,
                        'quantity': 1
                    }]
                }
            })
        })
    await Config.BOT.send_invoice(**invoice_params)