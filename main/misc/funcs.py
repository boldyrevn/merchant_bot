from typing import Sequence

from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram import Bot


async def set_commands(bot: Bot) -> None:
    commands = [
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
    profile_text = f"<strong>{roles[data['type']]}</strong> (добавлен админом: @{data['admin_username']})\n" \
                   f"<em>Имя</em>: {data['name']}\n" \
                   f"<em>Юзернейм</em>: {data['username']}\n" \
                   f"<em>Список стран</em>:\n" \
                   f"{countries_list}\n" \
                   f"<em>Описание</em>: {data['description']}\n"
    return profile_text


def show_profile_db(data: dict) -> str:
    profile_text = show_profile(data)
    if data['partner_id'] is None:
        profile_text += "<em>Ни с кем не срощен\n</em>"
    else:
        countries_list = '\n'.join([f'▪️ {country}' for country in data['merged_countries']])
        partner_string = f'<em>Срощен с</em> "{data["partner_name"]}" {data["partner_username"]} по странам:\n' \
                         f'{countries_list}\n'
        profile_text += partner_string
    if data['in_search']:
        profile_text += "<em>Поиск по странам включен</em>"
    else:
        profile_text += "<em>Поиск по странам выключен</em>"
    return profile_text


def show_matched_traders(traders: list[tuple[str, str]]) -> str:
    traders_list = '\n'.join([f'{i + 1}. <em>Трейдер</em> "{trader[0]}": {trader[1]}'
                              for i, trader in enumerate(traders)])
    answer_string = f"<strong>Совпадения:</strong>\n" \
                    f"{traders_list}"
    return answer_string


def show_matched_merchants(merchants: list[tuple[str, str, str]]) -> str:
    roles = {"merchant": "Мерчант", "platform": "Площадка"}
    merchants_list = '\n'.join([f'{i + 1}. <em>{roles[merch[0]]}</em> "{merch[1]}": {merch[2]}'
                                for i, merch in enumerate(merchants)])
    answer_string = f"<strong>Совпадения:</strong>\n" \
                    f"{merchants_list}"
    return answer_string


def show_matches(matches: list[Sequence[str]]) -> str:
    if len(matches) == 0:
        return "<strong>Совпадений нет</strong>"
    types = {"merchant": "мерчант", "platform": "площадка"}
    match_list = '\n'.join([f'<strong>{i + 1}.</strong> <em>{types[match[0]]}</em> "{match[1]}" '
                            f'- <em>трейдер</em> "{match[2]}": {match[3]}'
                            for i, match in enumerate(matches)])
    return f"<strong>Совпадения:</strong>\n{match_list}"
