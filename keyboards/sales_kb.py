from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from config import SUPPORT_BOT_USERNAME


def buyer_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💰 Купить", callback_data="buyer_buy")
    b.button(text="🎁 Подарить", callback_data="buyer_gift")
    b.button(text="❓ Спросить", url=f"https://t.me/{SUPPORT_BOT_USERNAME}")
    b.adjust(3)
    return b.as_markup()


def groups_list_kb(groups: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
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
        nav.append(("⬅️", f"groups_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("➡️", f"groups_page:{page + 1}"))
    for text, cb in nav:
        b.button(text=text, callback_data=cb)
    b.adjust(1)
    return b.as_markup()


def redirect_support_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🤖 Мой собрат", url=f"https://t.me/{SUPPORT_BOT_USERNAME}")
    return b.as_markup()


def _format_age(created: datetime) -> str:
    delta = datetime.now() - created
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"{days}д {hours}ч"
    return f"{hours}ч"
