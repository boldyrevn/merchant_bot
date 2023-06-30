from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram import Bot


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


def show_profile(data: dict) -> str:
    roles = {"merchant": "Мерчант", "platform": "Площадка", "trader": "Трейдер"}
    countries_list = '\n'.join([f'▪ {country}' for country in data['countries']])
    profile_text = f"<strong>{roles[data['entity_type']]}</strong>\n" \
                   f"<em>Имя</em>: {data['name']}\n" \
                   f"<em>Юзернейм</em>: {data['username']}\n" \
                   f"<em>Список стран</em>:\n" \
                   f"{countries_list}\n" \
                   f"<em>Описание</em>: {data['description']}"

    return profile_text
