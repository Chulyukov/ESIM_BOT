import json
from math import ceil

import shortuuid
from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, BufferedInputFile

from config import Config
from core.helpful_methods import (
    get_bundle_price_list, build_keyboard, generate_qr_code
)
from db.db_queries import db_get_emoji, db_get_ru_name
from monty_api import MontyApiAsync

router = Router()


@router.callback_query(F.data == "buy_esim")
@router.message(Command("buy_esim"))
async def buy_esim(msg: Message | CallbackQuery):
    """Отображение выбора направлений."""
    message_text = (
        "🚨 *Перед тем, как выбрать направление, "
        "удостоверьтесь, что ваш смартфон поддерживает eSIM.* "
        "[Инструкция](https://telegra.ph/Kak-ponyat-chto-u-menya-est-vozmozhnost-podklyuchit-eSIM-07-27).\n\n"
        "🆘 Если у вас возникли сложности, свяжитесь со "
        "[службой заботы клиента](https://t.me/esim_unity_support).\n\n"
        "👇 *Выберите интересующую вас страну.*"
    )
    kb = build_keyboard([
        InlineKeyboardButton(text="🇹🇷Турция", callback_data="country_turkey"),
        InlineKeyboardButton(text="🇹🇭Таиланд", callback_data="country_thailand"),
        InlineKeyboardButton(text="🇪🇬Египет", callback_data="country_egypt"),
        InlineKeyboardButton(text="🇦🇪ОАЭ", callback_data="country_united_arab_emirates"),
        InlineKeyboardButton(text="🇮🇹Италия", callback_data="country_italy"),
        InlineKeyboardButton(text="🇬🇷Греция", callback_data="country_greece"),
        InlineKeyboardButton(text="🇪🇸Испания", callback_data="country_spain"),
        InlineKeyboardButton(text="🇨🇾Кипр", callback_data="country_cyprus"),
        InlineKeyboardButton(text="🇫🇷Франция", callback_data="country_france"),
        InlineKeyboardButton(text="🇻🇳Вьетнам", callback_data="country_vietnam"),
        InlineKeyboardButton(text="🇮🇳Индия", callback_data="country_india"),
        InlineKeyboardButton(text="🇨🇳Китай", callback_data="country_china"),
        InlineKeyboardButton(text="🇲🇦Марокко", callback_data="country_morocco"),
        InlineKeyboardButton(text="🇮🇩Индонезия", callback_data="country_indonesia"),
        InlineKeyboardButton(text="🇨🇿Чехия", callback_data="country_czech_republic"),
        InlineKeyboardButton(text="🇬🇪Грузия", callback_data="country_georgia"),
        InlineKeyboardButton(text="🇯🇵Япония", callback_data="country_japan"),
        InlineKeyboardButton(text="🇱🇰Шри-Ланка", callback_data="country_sri_lanka"),
    ], (2,))

    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(text=message_text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await msg.answer(text=message_text, reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data.startswith("country_"))
async def choose_plan(callback: CallbackQuery):
    downloading_message = await callback.message.edit_text("*🚀 Подождите, загружаю данные...*")
    country = callback.data.split("country_")[1].replace("_", " ")
    prices = await get_bundle_price_list(country)

    buttons = [
        InlineKeyboardButton(text=f"{gb} ГБ - {ceil(price)} RUB",
                             callback_data=f"pay_{gb}_{country.replace(" ", "_")}_{ceil(price)}")
        for gb, price in prices.items()
    ]
    buttons.append(InlineKeyboardButton(text="⏪ К выбору страны", callback_data="buy_esim"))
    kb = build_keyboard(buttons, layout=(2,))

    emoji = db_get_emoji(country)
    ru_name = db_get_ru_name(country)

    await downloading_message.delete()
    await callback.message.answer(
        text=(
            f"*Страна:* {emoji}{ru_name.title()}"
            f"\n\n🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со [службой заботы клиента]({Config.SUPPORT_LINK})"
            "\n\n*👇 Выберите интересующий вас пакет интернета.*"
        ),
        reply_markup=kb,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith("pay_"))
async def pay_rub(callback: CallbackQuery, state: FSMContext):
    gb_amount = int(callback.data.split("_")[1])
    country = callback.data.split("_")[2]
    amount = int(callback.data.split("_")[-1])
    uuid = shortuuid.uuid()

    await state.update_data(uuid=uuid, gb_amount=gb_amount, country=country)

    emoji = db_get_emoji(country)
    ru_name = db_get_ru_name(country).capitalize()

    prices = [
        types.LabeledPrice(label=f'{emoji}{ru_name} - {gb_amount}ГБ', amount=amount * 100)
    ]

    provider_data = {
        "invoice": {
            "description": "Оплата через Telegram бота",
            "orderNo": uuid
        },
        "receipt": {
            "client": {
                "email": "esim.unity@mail.ru"
            },
            "items": [
                {
                    "name": f"{emoji}{ru_name} - {gb_amount}ГБ",
                    "quantity": 1.0,
                    "price": amount,
                    "vatType": "None",
                    "paymentSubject": "Commodity",
                    "paymentMethod": "FullPrepayment"
                }
            ]
        }
    }

    await Config.BOT.send_invoice(
        callback.from_user.id,
        title=f'{emoji}{ru_name} - {gb_amount}ГБ',
        description='Покупка пакета интернета',
        provider_token=Config.PAYMASTER_TOKEN_TEST,
        currency="rub",
        prices=prices,
        payload="invoice-payload",
        need_email=True,
        send_email_to_provider=True,
        provider_data=json.dumps(provider_data)
    )


@router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await Config.BOT.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    monty = MontyApiAsync()
    bundle_code = await monty.get_necessary_bundle_code(user_data["country"], user_data["gb_amount"])
    await monty.activate_esim(bundle_code, user_data["uuid"])
    esim_info = await monty.get_esim_info(user_data["uuid"])
    qr_code = await generate_qr_code(esim_info["activation_code"])
    document = BufferedInputFile(qr_code.getvalue(), filename="qr_code.png")

    await Config.BOT.send_document(
        chat_id=message.chat.id,
        document=document,
        caption=(
            "*🎊 Поздравляем с приобретением вашей первой eSIM!*"
            f"\n\n📛 *Название вашей eSIM:* `{user_data['country'].title()} - {user_data['uuid'][-4:]}`"
            f"\n🔗 *Ссылка для установки на iOS:* https://esimsetup.apple.com/esim_qrcode_provisioning?carddata={esim_info['activation_code']}"
            "\n\n📖 *Инструкции по установке:*"
            " [iPhone](https://telegra.ph/Kak-podklyuchit-eSIM-na-iPhone-07-27)"
            " | [Android](https://telegra.ph/Kak-podklyuchit-eSIM-na-Android-08-18)"
            " | [Samsung](https://telegra.ph/Kak-podklyuchit-eSIM-na-Samsung-08-18)"
            f"\n\n🏝️ *Сложности? Обратитесь в службу заботы клиента eSIM Unity* {Config.SUPPORT_SIMPLE_LINK}"
        )
    )
