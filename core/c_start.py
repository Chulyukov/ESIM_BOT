from datetime import datetime

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.helpful_methods import get_username, choose_direction, build_keyboard
from db.countries.db_countries import db_get_all_coincidences_by_search
from db.db_start import db_check_user_exist, db_add_user

router = Router()


@router.message()
async def deep_search(message: Message):
    user_text = message.text.lower()
    coincidences = db_get_all_coincidences_by_search(user_text)
    if coincidences:
        buttons = [InlineKeyboardButton(text=f"{data["emoji"]} {data["ru_name"].title()}", callback_data=f"choose_payment_method_{name}")
                   for name, data in coincidences.items()]
        buttons.append(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim"))
        kb = build_keyboard(buttons, (1,))
        await message.answer(text="*🔍 Результаты поиска*", reply_markup=kb)
    else:
        kb = InlineKeyboardBuilder().add(InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim")).as_markup()
        await message.reply("*Совпадений не найдено.*", reply_markup=kb)


@router.message(CommandStart)
async def start_command(message: Message, state: FSMContext):
    """/start"""
    await state.clear()
    is_user_exist = db_check_user_exist(str(message.chat.id))
    if is_user_exist:
        await message.answer(text="👋 *Добро пожаловать в нашего бота по работе с eSIM!*"
                             "\n\n📶 Этот бот занимается выдачей eSIM разных стран, чтобы у вас была возможность выйти в Интернет из любой точки мира."
                             "\n\n🌍 *Доступно более 170 направлений!*"
                             "\n\n👉Нажмите /buy\_esim, чтобы запустить процедуру покупки eSIM,"
                             " а все доступные команды бота доступны по команде /menu!")
    else:
        db_add_user(str(message.chat.id), get_username(message), datetime.now())
        await choose_direction(message)




