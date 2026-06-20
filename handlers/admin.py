import os
import math
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

import database
import telethon_manager
from config import ADMIN_ID, GROUPS_PER_PAGE
from states import AddAccountStates, CreateGroupStates
from keyboards.admin_kb import (
    admin_main_kb, cancel_kb, back_cancel_kb,
    group_type_kb, avatar_kb, description_kb,
    confirm_request_kb, groups_admin_list_kb,
    _format_age,
)

router = Router()
router.message.filter(F.from_user.id == ADMIN_ID)
router.callback_query.filter(F.from_user.id == ADMIN_ID)

_temp_group: dict = {}


async def _safe_edit(cb: CallbackQuery, text: str, **kwargs):
    try:
        await cb.message.edit_text(text, **kwargs)
    except TelegramBadRequest:
        pass


@router.message(Command("start"))
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👑 Панель администратора", reply_markup=admin_main_kb())


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    _temp_group.pop(cb.from_user.id, None)
    await telethon_manager.cancel_auth(cb.from_user.id)
    await _safe_edit(cb, "❌ Отменено")
    await cb.message.answer("👑 Панель администратора", reply_markup=admin_main_kb())
    await cb.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    _temp_group.pop(cb.from_user.id, None)
    await telethon_manager.cancel_auth(cb.from_user.id)
    await _safe_edit(cb, "👑 Панель администратора", reply_markup=admin_main_kb())
    await cb.answer()


@router.callback_query(F.data == "admin_add_account")
async def add_account_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddAccountStates.waiting_session_name)
    await _safe_edit(
        cb,
        "📝 Введите имя сессии (например: <code>account1</code>):",
        reply_markup=cancel_kb()
    )
    await cb.answer()


@router.message(AddAccountStates.waiting_session_name)
async def add_session_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name.replace("_", "").replace("-", "").isalnum():
        await message.answer("❌ Только буквы, цифры, _ и -. Попробуйте ещё раз:", reply_markup=cancel_kb())
        return
    await state.update_data(session_name=name)
    await state.set_state(AddAccountStates.waiting_api_id)
    await message.answer("🔑 Введите <b>API ID</b> с my.telegram.org:", reply_markup=cancel_kb())


@router.message(AddAccountStates.waiting_api_id)
async def add_api_id(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("❌ API ID должен быть числом:", reply_markup=cancel_kb())
        return
    await state.update_data(api_id=int(text))
    await state.set_state(AddAccountStates.waiting_api_hash)
    await message.answer("🔑 Введите <b>API Hash</b> с my.telegram.org:", reply_markup=cancel_kb())


@router.message(AddAccountStates.waiting_api_hash)
async def add_api_hash(message: Message, state: FSMContext):
    await state.update_data(api_hash=message.text.strip())
    await state.set_state(AddAccountStates.waiting_phone)
    await message.answer("📱 Введите номер телефона в формате <code>+79001234567</code>:", reply_markup=cancel_kb())


@router.message(AddAccountStates.waiting_phone)
async def add_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.startswith("+"):
        await message.answer("❌ Укажите номер с + (например +79001234567):", reply_markup=cancel_kb())
        return

    data = await state.get_data()
    msg = await message.answer("⏳ Отправляю код...")

    status, result = await telethon_manager.start_auth(
        admin_id=message.from_user.id,
        session_name=data["session_name"],
        api_id=data["api_id"],
        api_hash=data["api_hash"],
        phone=phone,
    )

    if status == "exists":
        await state.clear()
        await msg.edit_text(
            f"✅ Сессия уже авторизована — аккаунт <b>@{result}</b> добавлен!",
            reply_markup=admin_main_kb()
        )
    elif status is True:
        await state.update_data(phone=phone)
        await state.set_state(AddAccountStates.waiting_code)
        await msg.edit_text(
            f"✅ Код отправлен на <code>{phone}</code>\n\nВведите код через пробел (<code>1 2 3 4 5</code>):",
            reply_markup=cancel_kb()
        )
    else:
        await state.clear()
        await msg.edit_text(f"❌ Ошибка: {result}", reply_markup=admin_main_kb())


@router.message(AddAccountStates.waiting_code)
async def add_code(message: Message, state: FSMContext):
    code = message.text.strip().replace(" ", "")
    status, result = await telethon_manager.confirm_code(message.from_user.id, code)

    if status == "2fa":
        await state.set_state(AddAccountStates.waiting_password)
        await message.answer("🔐 Требуется пароль двухфакторной аутентификации:", reply_markup=cancel_kb())
    elif status == "retry":
        await message.answer(f"❌ {result}", reply_markup=cancel_kb())
    elif status is True:
        username = await telethon_manager.finalize_auth(message.from_user.id)
        await state.clear()
        await message.answer(
            f"✅ Аккаунт <b>@{username}</b> успешно добавлен!",
            reply_markup=admin_main_kb()
        )
    else:
        await state.clear()
        await telethon_manager.cancel_auth(message.from_user.id)
        await message.answer(f"❌ Ошибка: {result}", reply_markup=admin_main_kb())


@router.message(AddAccountStates.waiting_password)
async def add_password(message: Message, state: FSMContext):
    status, result = await telethon_manager.confirm_password(message.from_user.id, message.text.strip())

    if status is True:
        username = await telethon_manager.finalize_auth(message.from_user.id)
        await state.clear()
        await message.answer(f"✅ Аккаунт <b>@{username}</b> добавлен!", reply_markup=admin_main_kb())
    else:
        await message.answer(f"❌ Неверный пароль: {result}", reply_markup=cancel_kb())


@router.callback_query(F.data == "admin_create_group")
async def create_group_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CreateGroupStates.waiting_name)
    _temp_group[cb.from_user.id] = {}
    await _safe_edit(cb, "📝 Введите название группы:", reply_markup=cancel_kb())
    await cb.answer()


@router.message(CreateGroupStates.waiting_name)
async def create_group_name(message: Message, state: FSMContext):
    _temp_group[message.from_user.id]["name"] = message.text.strip()
    await state.set_state(CreateGroupStates.waiting_type)
    await message.answer("🔓 Тип группы:", reply_markup=group_type_kb())


@router.callback_query(F.data.in_({"group_type_open", "group_type_closed"}))
async def create_group_type(cb: CallbackQuery, state: FSMContext):
    _temp_group[cb.from_user.id]["is_open"] = cb.data == "group_type_open"
    await state.set_state(CreateGroupStates.waiting_avatar)
    await _safe_edit(cb, "🖼 Нужна ли аватарка?", reply_markup=avatar_kb())
    await cb.answer()


@router.callback_query(F.data == "avatar_no")
async def create_group_avatar_no(cb: CallbackQuery, state: FSMContext):
    _temp_group[cb.from_user.id]["avatar_path"] = None
    await state.set_state(CreateGroupStates.waiting_description)
    await _safe_edit(cb, "📄 Введите описание или пропустите:", reply_markup=description_kb())
    await cb.answer()


@router.callback_query(F.data == "avatar_yes")
async def create_group_avatar_yes(cb: CallbackQuery, state: FSMContext):
    await _safe_edit(cb, "📸 Отправьте фото для аватарки:", reply_markup=back_cancel_kb())
    await cb.answer()


@router.message(CreateGroupStates.waiting_avatar, F.photo)
async def create_group_avatar_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    avatar_path = f"/tmp/avatar_{message.from_user.id}.jpg"
    await message.bot.download_file(file.file_path, destination=avatar_path)
    _temp_group[message.from_user.id]["avatar_path"] = avatar_path
    await state.set_state(CreateGroupStates.waiting_description)
    await message.answer("📄 Введите описание или пропустите:", reply_markup=description_kb())


@router.callback_query(F.data == "desc_skip")
async def create_group_desc_skip(cb: CallbackQuery, state: FSMContext):
    _temp_group[cb.from_user.id]["description"] = None
    await cb.answer()
    await _do_create_group(cb.message, cb.from_user.id, state)


@router.message(CreateGroupStates.waiting_description)
async def create_group_description(message: Message, state: FSMContext):
    _temp_group[message.from_user.id]["description"] = message.text.strip()
    await _do_create_group(message, message.from_user.id, state)


async def _do_create_group(source: Message, admin_id: int, state: FSMContext):
    data = _temp_group.get(admin_id, {})
    name = data.get("name", "Без названия")
    is_open = data.get("is_open", True)
    description = data.get("description")
    avatar_path = data.get("avatar_path")
    has_avatar = avatar_path is not None

    msg = await source.answer("⏳ Создаю группу...")

    try:
        telegram_id, link = await telethon_manager.create_group(name, is_open, description, avatar_path)
        account = await database.get_active_account()
        group_id = await database.add_group(
            telegram_id=telegram_id,
            name=name,
            link=link,
            description=description,
            has_avatar=has_avatar,
            is_open=is_open,
            account_id=account["id"] if account else None,
        )
        group = await database.get_group(group_id)
        created = datetime.fromisoformat(group["created_at"])

        account_info = f"@{account['username']}" if account and account.get("username") else "неизвестно"
        type_str = "Открытая" if is_open else "Закрытая"
        avatar_str = "✅ Есть" if has_avatar else "❌ Нет"
        desc_str = description or "Нет"

        await msg.edit_text(
            f"✅ Группа создана!\n\n"
            f"📌 Название: {name}\n"
            f"🔗 Ссылка: {link}\n"
            f"🔓 Тип: {type_str}\n"
            f"🖼 Аватарка: {avatar_str}\n"
            f"📄 Описание: {desc_str}\n"
            f"🕐 Создана: {created.strftime('%d.%m.%Y %H:%M')}\n"
            f"👤 Аккаунт: {account_info}",
            reply_markup=admin_main_kb()
        )

        if avatar_path and os.path.exists(avatar_path):
            os.remove(avatar_path)

    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при создании: {e}", reply_markup=admin_main_kb())

    _temp_group.pop(admin_id, None)
    await state.clear()


@router.callback_query(F.data == "admin_delete_group")
async def delete_group_start(cb: CallbackQuery):
    groups = await database.get_all_groups()
    if not groups:
        await _safe_edit(cb, "📭 Нет групп для удаления.", reply_markup=admin_main_kb())
        await cb.answer()
        return

    total_pages = math.ceil(len(groups) / GROUPS_PER_PAGE)
    page_groups = groups[:GROUPS_PER_PAGE]
    await _safe_edit(
        cb,
        "🗑 Выберите группу для удаления:",
        reply_markup=groups_admin_list_kb(page_groups, 0, total_pages)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin_groups_page:"))
async def delete_group_page(cb: CallbackQuery):
    page = int(cb.data.split(":")[1])
    groups = await database.get_all_groups()
    total_pages = math.ceil(len(groups) / GROUPS_PER_PAGE)
    start = page * GROUPS_PER_PAGE
    page_groups = groups[start:start + GROUPS_PER_PAGE]
    try:
        await cb.message.edit_reply_markup(
            reply_markup=groups_admin_list_kb(page_groups, page, total_pages)
        )
    except TelegramBadRequest:
        pass
    await cb.answer()


@router.callback_query(F.data.startswith("delete_group_confirm:"))
async def delete_group_confirm(cb: CallbackQuery):
    group_id = int(cb.data.split(":")[1])
    group = await database.get_group(group_id)
    if not group:
        await cb.answer("❌ Группа не найдена", show_alert=True)
        return

    if group.get("telegram_id"):
        await telethon_manager.delete_telegram_group(group["telegram_id"])

    await database.delete_group(group_id)
    await _safe_edit(cb, f"✅ Группа «{group['name']}» удалена.", reply_markup=admin_main_kb())
    await cb.answer()


@router.callback_query(F.data == "admin_buyers")
async def admin_buyers(cb: CallbackQuery, bot: Bot):
    requests = await database.get_pending_requests()

    if not requests:
        await _safe_edit(cb, "📭 Нет новых заявок.", reply_markup=admin_main_kb())
        await cb.answer()
        return

    await _safe_edit(cb, f"👥 Заявки на покупку ({len(requests)} шт.):", reply_markup=admin_main_kb())

    for req in requests:
        username = f"@{req['username']}" if req.get("username") else "нет"
        full_name = f"{req.get('first_name', '')} {req.get('last_name', '')}".strip() or "нет"
        created = datetime.fromisoformat(req["created_at"])
        group_created = datetime.fromisoformat(req["group_created_at"])
        group_age = _format_age(group_created)

        text = (
            f"🆕 Новая заявка\n\n"
            f"👤 Имя: {full_name}\n"
            f"🆔 ID: {req['user_id']}\n"
            f"📎 Username: {username}\n\n"
            f"📦 Группа: {req['group_name']} ({group_age})\n"
            f"🔗 Ссылка: {req.get('group_link', 'нет')}\n"
            f"📅 Заявка: {created.strftime('%d.%m.%Y %H:%M')}"
        )
        await bot.send_message(
            cb.from_user.id,
            text,
            reply_markup=confirm_request_kb(req["id"])
        )

    await cb.answer()


@router.callback_query(F.data.startswith("confirm_purchase:"))
async def confirm_purchase(cb: CallbackQuery, bot: Bot):
    request_id = int(cb.data.split(":")[1])
    req = await database.get_request(request_id)
    if not req:
        await cb.answer("❌ Заявка уже обработана", show_alert=True)
        try:
            await cb.message.delete()
        except TelegramBadRequest:
            pass
        return

    group = await database.get_group(req["group_id"])

    await database.delete_request(request_id)
    await database.set_group_for_sale(req["group_id"], False)

    try:
        await cb.message.edit_text(f"✅ Заявка #{request_id} подтверждена — добавляю покупателя в группу...")
    except TelegramBadRequest:
        pass

    if group and group.get("telegram_id"):
        await telethon_manager.sell_group(
            telegram_id=group["telegram_id"],
            buyer_user_id=req["user_id"],
            buyer_username=req.get("username"),
            account_id=group.get("account_id") or 0,
        )

    await bot.send_message(
        req["user_id"],
        "🎉 Оу, та ты счастливчик — теперь группа твоя!\n\nТы добавлен и получил права администратора. Удачи 🚀"
    )
    await cb.answer()


@router.callback_query(F.data.startswith("reject_purchase:"))
async def reject_purchase(cb: CallbackQuery, bot: Bot):
    request_id = int(cb.data.split(":")[1])
    req = await database.get_request(request_id)
    if not req:
        await cb.answer("❌ Заявка уже обработана", show_alert=True)
        try:
            await cb.message.delete()
        except TelegramBadRequest:
            pass
        return

    await database.delete_request(request_id)
    try:
        await cb.message.edit_text(f"❌ Заявка #{request_id} отклонена")
    except TelegramBadRequest:
        pass
    await bot.send_message(
        req["user_id"],
        "😅 Ну ничего, зато в тюрьму не залетел — не падай духом, удачи! 💪"
    )
    await cb.answer()