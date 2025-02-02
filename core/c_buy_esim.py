from math import ceil

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton

from config import Config
from core.helpful_methods import (
    get_bundle_price_list, build_keyboard, get_bundle_code
)
from db.db_queries import db_update_data_country, db_get_emoji, db_get_ru_name

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
    db_update_data_country(callback.message.chat.id, country)
    prices = get_bundle_price_list(country)

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
async def pay_rub(callback: CallbackQuery):
    downloading_message = await callback.message.answer("*🚀 Подождите, загружаю данные...*")
    gb_amount = callback.data.split("_")[1]
    price = callback.data.split("_")[-1]
    country = ' '.join(callback.data.split("_")[2:-1])
    bundle_code = get_bundle_code(country, gb_amount).replace("_", "\_")

    emoji = db_get_emoji(country)
    ru_name = db_get_ru_name(country)

    await downloading_message.delete()
    await callback.message.answer(text=f"*Страна:* {emoji}{ru_name.title()}"
                                       f"\n*Цена:* {price} RUB"
                                       f"\n*Пакет интернета:* {gb_amount} GB"
                                       f"\n*Код продукта:* {bundle_code}"
                                       "\n\n🛑 Оплата временно недоступна, но вы можете приобрести нужный тариф,"
                                       f" обратившись в [службу заботы клиента]({Config.SUPPORT_LINK})."
                                       f" Просто перешлите это сообщение поддержке.")
    # await prepare_payment_order(callback, "RUB")