from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import Config
from core.commands.buy_esim.buy_esim_service import buy_esim_service, choose_payment_method_service, \
    choose_plan_russian_service, choose_plan_star_service, pay_russian_card_service, pay_star_service, \
    calculate_successfull_payment
from core.status import remember_country

router = Router()


@router.message(Command("buy_esim"))
async def buy_esim(message: Message):
    await buy_esim_service(message)


@router.callback_query(F.data == "buy_esim")
async def buy_esim(message: Message, state: FSMContext):
    await state.clear()
    await buy_esim_service(message)


@router.callback_query(F.data.startswith("choose_payment_method_"))
async def choose_payment_method(callback: CallbackQuery):
    await choose_payment_method_service(callback)


@router.callback_query(F.data == "choose_plan_russian_card")
async def choose_plan_russian_card(callback: CallbackQuery):
    await choose_plan_russian_service(callback)


@router.callback_query(F.data == "choose_plan_star")
async def choose_plan_star_card(callback: CallbackQuery):
    await choose_plan_star_service(callback)


@router.callback_query(F.data.startswith("pay_rub_"))
async def pay_russian_card(callback: CallbackQuery):
    await pay_russian_card_service(callback)


@router.callback_query(F.data.startswith("pay_stars_"))
async def pay_star(callback: CallbackQuery):
    await pay_star_service(callback)


@router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await Config.BOT.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    await calculate_successfull_payment(message)
