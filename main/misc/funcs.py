from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram import Bot

from typing import List


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начало работы"),
        BotCommand(command="reset", description="Отменяет изменения и возвращает в главное меню")
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())


def format_country(country: str) -> str:
    country = country.strip().lower()
    country = country[0].upper() + country[1:]
    return country
