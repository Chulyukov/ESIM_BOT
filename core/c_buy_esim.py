from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from core.helpful_methods import (
    get_plan_prices, build_keyboard, prepare_payment_order, choose_direction
)
from db.db_queries import db_get_20_countries, db_update_data_country, db_get_regions

router = Router()

# Общие константы
SUPPORT_LINK = "[службой заботы клиента](https://t.me/esim_unity_support)"
COMMON_TEXT = (
    "🆘 Если у вас возникли какие-либо сложности, пожалуйста, свяжитесь со "
    f"{SUPPORT_LINK}."
)


# Хендлеры для основных действий
@router.callback_query(F.data == "buy_esim")
@router.message(Command("buy_esim"))
async def buy_esim(msg: Message | CallbackQuery):
    await choose_direction(msg)


@router.callback_query(F.data == "popular_directions")
async def choose_popular_direction(callback: CallbackQuery):
    popular_countries = [
        ("🇹🇷 Турция", "choose_plan_rub_turkey"),
        ("🇹🇭 Тайланд", "choose_plan_rub_thailand"),
        ("🇦🇪 Объединенные Арабские Эмираты", "choose_plan_rub_united_arab_emirates"),
        ("🇪🇬 Египет", "choose_plan_rub_egypt"),
        ("🇬🇷 Греция", "choose_plan_rub_greece"),
        ("🇻🇳 Вьетнам", "choose_plan_rub_vietnam"),
        ("🇪🇸 Испания", "choose_plan_rub_spain"),
        ("🇮🇩 Индонезия", "choose_plan_rub_indonesia"),
        ("🇨🇳 Китай", "choose_plan_rub_china"),
        ("🇨🇾 Кипр", "choose_plan_rub_cyprus"),
    ]

    buttons = [
        InlineKeyboardButton(text=text, callback_data=data) for text, data in popular_countries
    ]
    buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
    kb = build_keyboard(buttons, layout=(2, 2, 2, 2, 2, 1))

    await callback.message.edit_text(
        text=f"{COMMON_TEXT}\n\n*👇 Выберите конкретное направление.*",
        reply_markup=kb,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith("countries_"))
async def choose_concrete_direction(callback: CallbackQuery):
    pages_to_skip = int(callback.data.split("_")[-1])
    countries = db_get_20_countries(pages_to_skip)
    next_countries = db_get_20_countries(pages_to_skip + 1)

    buttons = [
        InlineKeyboardButton(
            text=f"{emoji} {ru_name.title()}",
            callback_data=f"choose_plan_rub_{name.replace(' ', '_')}"
        )
        for name, ru_name, emoji in countries
    ]

    navigation_buttons = []
    if pages_to_skip > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⏮️ Назад", callback_data=f"countries_{pages_to_skip - 1}"))
    if next_countries:
        navigation_buttons.append(InlineKeyboardButton(text="⏭️ Дальше", callback_data=f"countries_{pages_to_skip + 1}"))
    navigation_buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
    buttons.extend(navigation_buttons)

    kb = build_keyboard(buttons, layout=(2,) * len(buttons[:-len(navigation_buttons)]) + (len(navigation_buttons),))
    await callback.message.edit_text(
        text=f"{COMMON_TEXT}\n\n*👇 Выберите страну.*",
        reply_markup=kb,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "regions")
async def choose_region(callback: CallbackQuery):
    regions = db_get_regions()
    buttons = [
        InlineKeyboardButton(
            text=f"{emoji} {ru_name.title()}",
            callback_data=f"choose_plan_rub_{name.replace(' ', '_')}"
        )
        for name, ru_name, emoji in regions
    ]
    buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
    kb = build_keyboard(buttons, layout=(1,))

    await callback.message.edit_text(
        text=(
            "*🌍 Узнайте, какие страны входят в региональные пакеты с интернетом в формате eSIM.*"
            "\nЭто поможет вам оставаться на связи в разных частях мира без лишних сложностей!"
            "\n\n*📱 Подробности в нашей статье по ссылке:*"
            "\n[Пакеты eSIM для разных регионов: доступные страны](https://telegra.ph/Pakety-eSIM-dlya-raznyh-regionov-dostupnye-strany-10-06)"
            f"\n\n{COMMON_TEXT}"
            "\n\n*✈️ Ознакомьтесь с доступными странами и выберите лучший пакет для вашего путешествия!*"
        ),
        reply_markup=kb,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "search")
async def search(callback: CallbackQuery):
    await callback.message.answer(
        "⌨️ В поле ввода сообщения вы можете ввести название интересующего вас направления."
    )


@router.callback_query(F.data.startswith("choose_plan_rub_"))
async def choose_plan_rub(callback: CallbackQuery):
    country = callback.data.split("choose_plan_rub_")[1]
    db_update_data_country(callback.message.chat.id, country.replace("_", " "))
    prices = get_plan_prices("RUB", callback.message.chat.id)

    buttons = [
        InlineKeyboardButton(text=f"{gb} ГБ - {price} RUB", callback_data=f"pay_rub_{gb}")
        for gb, price in prices.items()
    ]
    buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
    kb = build_keyboard(buttons, layout=(2, 2, 1))

    await callback.message.edit_text(
        text=(
            "💳 Оплачивая российской картой, вы соглашаетесь с"
            " [условиями использования сервиса](https://telegra.ph/Kak-proishodit-oplata-v-bote-09-05)."
            f"\n\n{COMMON_TEXT}"
            "\n\n*👇 Выберите интересующий вас пакет интернета.*"
        ),
        reply_markup=kb,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith("pay_rub_"))
async def pay_rub(callback: CallbackQuery):
    await prepare_payment_order(callback, "RUB")