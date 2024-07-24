from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from core.commands.buy_esim.buy_esim_service import buy_esim_service, choose_payment_method_service, \
    choose_plan_russian_service, choose_plan_star_service, pay_russian_card_service, pay_star_service
from core.status import remember_country

router = Router()


@router.message(Command("buy_esim"))
async def buy_esim(message: Message, state: FSMContext):
    await state.clear()
    await buy_esim_service(message)


@router.callback_query(F.data == "buy_esim")
async def buy_esim(message: Message, state: FSMContext):
    await state.clear()
    await buy_esim_service(message)


@router.callback_query(F.data.startswith("choose_payment_method_"))
async def choose_payment_method(callback: CallbackQuery, state: FSMContext):
    await remember_country(callback, state)
    await choose_payment_method_service(callback)


@router.callback_query(F.data == "choose_plan_russian_card")
async def choose_plan_russian_card(callback: CallbackQuery):
    await choose_plan_russian_service(callback)


@router.callback_query(F.data == "choose_plan_star")
async def choose_plan_star_card(callback: CallbackQuery):
    await choose_plan_star_service(callback)


@router.callback_query(F.data.startswith("pay_russian_card_"))
async def pay_russian_card(callback: CallbackQuery, state: FSMContext):
    await pay_russian_card_service(callback, state)


@router.callback_query(F.data.startswith("pay_star_"))
async def pay_star(callback: CallbackQuery, state: FSMContext):
    await pay_star_service(callback, state)

# TODO: Расписать все хэндеры для ру и стар оплаты с помощью запроса 4
# TODO: Добавить логику продления существующей esim с помощью запроса 6
