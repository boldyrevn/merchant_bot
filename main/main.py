import asyncio.exceptions
import os
from contextlib import suppress

import asyncpg
from aiogram import Bot, Dispatcher

from .handlers import root, add
from .misc import set_commands


async def on_start(bot: Bot):
    await set_commands(bot)


async def start() -> None:
    bot = Bot(token=os.environ['TOKEN_API'])
    dp = Dispatcher()
    root.include_router(add)
    dp.include_router(root)
    dp.startup.register(on_start)

    connection_pool: asyncpg.Pool = await asyncpg.create_pool(host="localhost", port=5432, user="merchant_bot",
                                                              database="merchant_bot_db", password="2112")

    with suppress(asyncio.exceptions.CancelledError, KeyboardInterrupt):
        await dp.start_polling(bot, connection_pool=connection_pool)
