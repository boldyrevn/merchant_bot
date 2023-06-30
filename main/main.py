import asyncio.exceptions
import os
from contextlib import suppress

import asyncpg
from aiogram import Bot, Dispatcher

from .database import DataBase
from .handlers import root, add
from .misc import set_commands


async def on_start(bot: Bot, db: DataBase):
    await db.init()
    await set_commands(bot)


async def on_shutdown(db: DataBase):
    await db.close_connection()


async def start() -> None:
    bot = Bot(token=os.environ['TOKEN_API'])
    dp = Dispatcher()
    connection = await asyncpg.connect(host="localhost", port=5432, user="merchant_bot",
                                       database="merchant_bot_db", password="2112")
    db = DataBase(connection)

    root.include_router(add)
    dp.include_router(root)

    dp.startup.register(on_start)
    dp.shutdown.register(on_shutdown)

    with suppress(asyncio.exceptions.CancelledError, KeyboardInterrupt):
        await dp.start_polling(bot, db=db)
