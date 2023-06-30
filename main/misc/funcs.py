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
    profile_text = f"<strong>{roles[data['type']]}</strong>\n" \
                   f"<em>Имя</em>: {data['name']}\n" \
                   f"<em>Юзернейм</em>: {data['username']}\n" \
                   f"<em>Список стран</em>:\n" \
                   f"{countries_list}\n" \
                   f"<em>Описание</em>: {data['description']}\n"
    return profile_text


def show_profile_db(data: dict) -> str:
    profile_text = show_profile(data)
    if not data['partners']:
        profile_text += "<em>Ни с кем не срощен</em>"
    else:
        partners_list = '\n'.join([f" - '{partner}'\n" for partner in data['partners']])
        profile_text += f"<em>Срощен с</em>:\n{partners_list}"
    return profile_text
