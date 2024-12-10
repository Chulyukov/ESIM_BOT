from datetime import datetime
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.helpful_methods import get_username, choose_direction, build_keyboard
from db.db_queries import db_get_all_coincidences_by_search, db_check_user_exist, db_add_user

router = Router()

# Константы для текстов сообщений
NO_RESULTS_TEXT = "*Совпадений не найдено.*"
SEARCH_RESULTS_TEXT = "*🔍 Результаты поиска*"

# Кнопка возврата
BACK_BUTTON = InlineKeyboardButton(text="⏪ К выбору направлений", callback_data="buy_esim")


@router.message(CommandStart)
async def start_command(message: Message, state: FSMContext):
    await state.clear()

    chat_id = str(message.chat.id)
    is_user_exist = db_check_user_exist(chat_id)

    if is_user_exist:
        user_text = message.text.lower()
        coincidences = db_get_all_coincidences_by_search(user_text)

        if coincidences:
            buttons = [
                InlineKeyboardButton(
                    text=f"{data['emoji']} {data['ru_name'].title()}",
                    callback_data=f"choose_plan_rub_{name}"
                )
                for name, data in coincidences.items()
            ]
            buttons.append(BACK_BUTTON)
            kb = build_keyboard(buttons, (1,))
            await message.answer(text=SEARCH_RESULTS_TEXT, reply_markup=kb)
        else:
            kb = InlineKeyboardBuilder().add(BACK_BUTTON).as_markup()
            await message.reply(NO_RESULTS_TEXT, reply_markup=kb)
    else:
        username = get_username(message)
        db_add_user(chat_id, username, datetime.now())
        await choose_direction(message)