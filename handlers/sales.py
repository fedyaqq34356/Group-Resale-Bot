import math
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database
import telethon_manager
from config import ADMIN_ID, GROUPS_PER_PAGE, CARD_NUMBER, SUPPORT_BOT_USERNAME
from states import BuyerStates
from keyboards.sales_kb import buyer_main_kb, groups_list_kb, redirect_support_kb

router = Router()
router.message.filter(F.from_user.id != ADMIN_ID)
router.callback_query.filter(F.from_user.id != ADMIN_ID)


@router.message(Command("start"))
async def buyer_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привет! Добро пожаловать!\n\nЧто вы хотите у нас найти?",
        reply_markup=buyer_main_kb()
    )


@router.callback_query(F.data == "buyer_buy")
async def buyer_buy(cb: CallbackQuery, state: FSMContext):
    groups = await database.get_groups_for_sale()
    if not groups:
        await cb.answer("😔 Пока нет доступных групп", show_alert=True)
        return

    total_pages = math.ceil(len(groups) / GROUPS_PER_PAGE)
    text = "🏪 Вот наши группы:\n\nНажмите на группу чтобы открыть её, затем введите её номер для покупки:"
    await cb.message.edit_text(
        text,
        reply_markup=groups_list_kb(groups, 0, total_pages)
    )
    await state.set_state(BuyerStates.waiting_group_number)
    await state.update_data(page=0)
    await cb.answer()


@router.callback_query(F.data.startswith("groups_page:"), BuyerStates.waiting_group_number)
async def groups_paginate(cb: CallbackQuery, state: FSMContext):
    page = int(cb.data.split(":")[1])
    groups = await database.get_groups_for_sale()
    total_pages = math.ceil(len(groups) / GROUPS_PER_PAGE)
    await cb.message.edit_reply_markup(
        reply_markup=groups_list_kb(groups, page, total_pages)
    )
    await state.update_data(page=page)
    await cb.answer()


@router.message(BuyerStates.waiting_group_number)
async def buyer_enter_number(message: Message, state: FSMContext):
    text = message.text.strip()

    if not text.isdigit():
        await message.answer(
            "🤖 Я занимаюсь только продажами — спроси у моего собрата:",
            reply_markup=redirect_support_kb()
        )
        return

    number = int(text)
    groups = await database.get_groups_for_sale()

    if number < 1 or number > len(groups):
        await message.answer(f"❌ Введите число от 1 до {len(groups)}:")
        return

    group = groups[number - 1]
    user = message.from_user

    request_id = await database.add_purchase_request(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        group_id=group["id"]
    )

    await state.clear()

    await message.answer(
        f"🔥 Оу оу, вижу ты серьёзно настроен!\n\n"
        f"💳 Давай ты группу оплатишь и сразу же сможешь пользоваться!\n\n"
        f"Оплати по номеру карты: <code>{CARD_NUMBER}</code>\n\n"
        f"⏳ И ожидай подтверждения...",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "buyer_gift")
async def buyer_gift(cb: CallbackQuery):
    username = await telethon_manager.get_active_client_username()
    telethon_manager.add_pending_gifter(cb.from_user.id)
    await cb.message.edit_text(
        f"🎁 Ты хочешь сделать мне подарок в виде группы?\n\n"
        f"Спасибо, дружище! Можешь пожалуйста перепишать группу моему компьютру:\n"
        f"<b>{username}</b>\n\n"
        f"Как только всё оформишь — я сразу это почувствую! 😊",
        parse_mode="HTML"
    )
    await cb.answer()
