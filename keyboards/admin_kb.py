from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime


def admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Добавить аккаунт Telethon", callback_data="admin_add_account")
    b.button(text="📁 Создать группу", callback_data="admin_create_group")
    b.button(text="🗑 Удалить группу", callback_data="admin_delete_group")
    b.button(text="👥 Покупатели", callback_data="admin_buyers")
    b.adjust(1)
    return b.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data="admin_cancel")
    return b.as_markup()


def back_cancel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Назад", callback_data="admin_back")
    b.button(text="❌ Отмена", callback_data="admin_cancel")
    b.adjust(2)
    return b.as_markup()


def group_type_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔓 Открытая", callback_data="group_type_open")
    b.button(text="🔒 Закрытая", callback_data="group_type_closed")
    b.button(text="❌ Отмена", callback_data="admin_cancel")
    b.adjust(2, 1)
    return b.as_markup()


def avatar_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Да", callback_data="avatar_yes")
    b.button(text="❌ Нет", callback_data="avatar_no")
    b.button(text="⬅️ Назад", callback_data="admin_back")
    b.adjust(2, 1)
    return b.as_markup()


def description_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➡️ Пропустить", callback_data="desc_skip")
    b.button(text="⬅️ Назад", callback_data="admin_back")
    b.adjust(2)
    return b.as_markup()


def confirm_request_kb(request_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Подтвердить", callback_data=f"confirm_purchase:{request_id}")
    b.button(text="❌ Отклонить", callback_data=f"reject_purchase:{request_id}")
    b.adjust(2)
    return b.as_markup()


def groups_admin_list_kb(groups: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for g in groups:
        created = datetime.fromisoformat(g["created_at"])
        age = _format_age(created)
        b.button(
            text=f"🗑 {g['name']} ({age})",
            callback_data=f"delete_group_confirm:{g['id']}"
        )
    nav = []
    if page > 0:
        nav.append(("⬅️", f"admin_groups_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("➡️", f"admin_groups_page:{page + 1}"))
    for text, cb in nav:
        b.button(text=text, callback_data=cb)
    b.button(text="❌ Отмена", callback_data="admin_cancel")
    b.adjust(1)
    return b.as_markup()


def _format_age(created: datetime) -> str:
    delta = datetime.now() - created
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"{days}д {hours}ч"
    return f"{hours}ч"
