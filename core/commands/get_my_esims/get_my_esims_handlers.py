
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from core.commands.get_my_esims.get_my_esims_service import get_my_esims_service, get_esim_info_service, \
    top_up_choose_payment_method_service, top_up_choose_plan_russian_service, top_up_choose_plan_star_service, \
    top_up_pay_russian_card_service, top_up_pay_star_service

router = Router()


@router.message(Command("get_my_esims"))
async def get_my_esims(message: Message):
    await get_my_esims_service(message)


@router.callback_query(F.data.startswith("get_esim_info_"))
async def get_esim_info(callback: CallbackQuery):
    await get_esim_info_service(callback)


@router.callback_query(F.data.startswith("top_up_choose_payment_method"))
async def top_up_choose_payment_method(callback: CallbackQuery):
    await top_up_choose_payment_method_service(callback)


@router.callback_query(F.data == "top_up_choose_plan_russian")
async def top_up_choose_plan_russian(callback: CallbackQuery):
    await top_up_choose_plan_russian_service(callback)


@router.callback_query(F.data == "top_up_choose_plan_star")
async def top_up_choose_plan_star(callback: CallbackQuery):
    await top_up_choose_plan_star_service(callback)


@router.callback_query(F.data.startswith("top_up_pay_rub_"))
async def top_up_pay_russian_card(callback: CallbackQuery):
    await top_up_pay_russian_card_service(callback)


@router.callback_query(F.data.startswith("top_up_pay_stars_"))
async def top_up_pay_star(callback: CallbackQuery):
    await top_up_pay_star_service(callback)
