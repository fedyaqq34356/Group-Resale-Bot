import math
import random
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database
from config import ADMIN_ID, GROUPS_PER_PAGE
from states import SupportStates, AdminSupportReplyStates
from keyboards.support_kb import (
    groups_support_list_kb, hang_up_kb,
    reply_to_user_kb, reply_to_admin_kb,
)

_RELAY_PHRASES = [
    "📡 Передаю боссу...",
    "🚀 Отправляю сообщение...",
    "📨 Связываюсь с командой...",
    "💼 Ваш вопрос уже летит к нужным людям...",
    "🎯 Цель захвачена, передаю...",
    "📞 Соединяю с боссом...",
    "🛸 Телепортирую ваш вопрос...",
    "🎩 Прошу минуту, сэр, разбираюсь...",
    "🧠 Обрабатываю запрос, как Сол Гудман дело...",
    "📝 Записал, передаю Джеймсу Макгиллу лично в руки...",
    "⚡ Молниеносно доставляю ваш запрос...",
    "🎪 Здесь Джимми МакГилл — одну секунду!",
    "📬 Кладу конвертик на стол босса...",
    "🔑 Открываю нужную дверь, подождите...",
    "🧩 Пазл складывается, сейчас передам...",
    "🎭 Лучший адвокат в Альбукерке уже в курсе...",
    "🌟 Ваш вопрос — моей команде приоритет номер один...",
    "🏛 Обращаюсь в высшие инстанции...",
    "💡 Решение близко, босс уже знает...",
    "🎸 Вопрос принят, передаю с рок-н-роллом...",
    "🌀 Закручиваю бюрократическое колесо...",
    "🔮 Мой хрустальный шар говорит — босс ответит...",
    "📺 Прерываем программу для важного сообщения...",
    "🦅 Орёл уже несёт ваш запрос...",
    "💼 Как говорит мой клиент — это всё законно...",
    "⏳ Ваш вопрос в хороших руках, клянусь...",
    "🗺 Прокладываю маршрут к ответу...",
    "🎬 Снято! Передаю в монтаж боссу...",
    "🍕 Даже pizza delivery быстрее не приедет...",
    "🌈 По ту сторону радуги вас уже ждут...",
]

support_user_router = Router()
support_user_router.message.filter(F.from_user.id != ADMIN_ID)
support_user_router.callback_query.filter(F.from_user.id != ADMIN_ID)

support_admin_router = Router()
support_admin_router.message.filter(F.from_user.id == ADMIN_ID)
support_admin_router.callback_query.filter(F.from_user.id == ADMIN_ID)


@support_user_router.message(Command("start"))
async def support_start(message: Message, state: FSMContext):
    await state.clear()
    groups = await database.get_groups_for_sale()
    if not groups:
        await message.answer(
            "👋 Приветствую! Мы уже виделись, не так ли? Да-да, в моём собрате!\n\n"
            "😔 К сожалению, сейчас нет доступных групп для обсуждения."
        )
        return

    total_pages = math.ceil(len(groups) / GROUPS_PER_PAGE)
    await message.answer(
        "👋 Приветствую! Мы уже виделись, не так ли?\n"
        "Да-да, в моём собрате — ну что ж, рад снова тебя видеть! 😊\n\n"
        "Выбирай, какой канал тебя интересует?",
        reply_markup=groups_support_list_kb(groups, 0, total_pages)
    )
    await state.set_state(SupportStates.waiting_group_number)


@support_user_router.callback_query(F.data.startswith("support_groups_page:"), SupportStates.waiting_group_number)
async def support_groups_paginate(cb: CallbackQuery, state: FSMContext):
    page = int(cb.data.split(":")[1])
    groups = await database.get_groups_for_sale()
    total_pages = math.ceil(len(groups) / GROUPS_PER_PAGE)
    await cb.message.edit_reply_markup(
        reply_markup=groups_support_list_kb(groups, page, total_pages)
    )
    await cb.answer()


@support_user_router.message(SupportStates.waiting_group_number)
async def support_enter_number(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("🔢 Пожалуйста, введите номер группы:")
        return

    number = int(text)
    groups = await database.get_groups_for_sale()

    if number < 1 or number > len(groups):
        await message.answer(f"❌ Введите число от 1 до {len(groups)}:")
        return

    group = groups[number - 1]
    await database.create_support_session(message.from_user.id, group["id"])
    await state.set_state(SupportStates.in_conversation)

    await message.answer(
        f"✅ Хорошо, я тебя понял!\n\n"
        f"📞 Напиши моему боссу — он тебе даст ответ.\n"
        f"Как закончите разговаривать, нажми кнопку снизу 👇",
        reply_markup=hang_up_kb()
    )

    user = message.from_user
    username = f"@{user.username}" if user.username else "нет"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "нет"

    await bot.send_message(
        ADMIN_ID,
        f"📞 Новый запрос в поддержку\n\n"
        f"👤 Имя: {full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📎 Username: {username}\n"
        f"📦 Группа: {group['name']}\n\n"
        f"💬 Пользователь готов общаться"
    )


@support_user_router.message(SupportStates.in_conversation, F.text == "📵 Повесить трубку")
async def support_hang_up(message: Message, state: FSMContext, bot: Bot):
    await database.close_session(message.from_user.id)
    await state.clear()

    await message.answer(
        "📵 Я думаю, у вас была отличная беседа!\n\n"
        "Ну что ж, передавай привет моему брату. Пока! 👋",
        reply_markup=ReplyKeyboardRemove()
    )

    user = message.from_user
    username = f"@{user.username}" if user.username else "нет"
    await bot.send_message(
        ADMIN_ID,
        f"📵 Пользователь {username} (ID: {user.id}) завершил разговор."
    )


@support_user_router.message(SupportStates.in_conversation)
async def support_user_message(message: Message, bot: Bot):
    user = message.from_user
    username = f"@{user.username}" if user.username else "нет"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "нет"

    phrase = random.choice(_RELAY_PHRASES)
    await message.answer(phrase)

    await bot.send_message(
        ADMIN_ID,
        f"💬 Сообщение от {full_name} ({username}, ID: {user.id}):\n\n{message.text}",
        reply_markup=reply_to_user_kb(user.id)
    )


@support_user_router.callback_query(F.data == "support_reply_admin", SupportStates.in_conversation)
async def user_reply_to_admin(cb: CallbackQuery, state: FSMContext):
    await cb.answer("✏️ Напишите ваш ответ в чат:")


@support_admin_router.callback_query(F.data.startswith("support_reply_user:"))
async def admin_reply_start(cb: CallbackQuery, state: FSMContext):
    user_id = int(cb.data.split(":")[1])
    await state.set_state(AdminSupportReplyStates.waiting_reply)
    await state.update_data(target_user_id=user_id)
    await cb.message.answer(f"✏️ Введите ответ пользователю {user_id}:")
    await cb.answer()


@support_admin_router.message(AdminSupportReplyStates.waiting_reply)
async def admin_send_reply(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    await state.clear()

    if not target_user_id:
        await message.answer("❌ Ошибка: неизвестный получатель.")
        return

    session = await database.get_active_session(target_user_id)
    if not session:
        await message.answer("ℹ️ Пользователь уже завершил разговор.")
        return

    await bot.send_message(
        target_user_id,
        f"📩 Ответ от босса:\n\n{message.text}",
        reply_markup=reply_to_admin_kb()
    )
    await message.answer("✅ Ответ отправлен.")
