from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from datetime import datetime


def groups_support_list_kb(groups: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    start = page * 5
    page_groups = groups[start:start + 5]
    for i, g in enumerate(page_groups, start=start + 1):
        created = datetime.fromisoformat(g["created_at"])
        age = _format_age(created)
        b.button(
            text=f"{i}. {g['name']} ({age})",
            url=g["link"] or "https://t.me"
        )
    nav = []
    if page > 0:
        nav.append(("⬅️", f"support_groups_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("➡️", f"support_groups_page:{page + 1}"))
    for text, cb in nav:
        b.button(text=text, callback_data=cb)
    b.adjust(1)
    return b.as_markup()


def hang_up_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text="📵 Повесить трубку")
    return b.as_markup(resize_keyboard=True)


def reply_to_user_kb(user_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="↩️ Ответить", callback_data=f"support_reply_user:{user_id}")
    return b.as_markup()


def reply_to_admin_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="↩️ Ответить", callback_data="support_reply_admin")
    return b.as_markup()


def _format_age(created: datetime) -> str:
    delta = datetime.now() - created
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"{days}д {hours}ч"
    return f"{hours}ч"
