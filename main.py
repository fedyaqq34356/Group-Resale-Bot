import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import bot_instances
import database
import telethon_manager
from config import SALES_BOT_TOKEN, SUPPORT_BOT_TOKEN
from handlers import admin, sales, support

logging.basicConfig(level=logging.INFO)


async def on_gift_received(user_id: int, group_name: str):
    if bot_instances.sales_bot:
        await bot_instances.sales_bot.send_message(
            user_id,
            f"💖 От сердца и почек дарю вам респект!\n\n"
            f"Группа «{group_name}» принята и выставлена на продажу.\n"
            f"Спасибо, друг — ты мне очень помог! 🙏"
        )


async def main():
    await database.init_db()

    sales_bot = Bot(
        token=SALES_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    support_bot = Bot(
        token=SUPPORT_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    bot_instances.sales_bot = sales_bot
    bot_instances.support_bot = support_bot

    telethon_manager.set_gift_callback(on_gift_received)
    await telethon_manager.load_clients()

    sales_dp = Dispatcher(storage=MemoryStorage())
    sales_dp.include_router(admin.router)
    sales_dp.include_router(sales.router)

    support_dp = Dispatcher(storage=MemoryStorage())
    support_dp.include_router(support.support_admin_router)
    support_dp.include_router(support.support_user_router)

    await asyncio.gather(
        sales_dp.start_polling(sales_bot, allowed_updates=["message", "callback_query"]),
        support_dp.start_polling(support_bot, allowed_updates=["message", "callback_query"]),
    )


if __name__ == "__main__":
    asyncio.run(main())
