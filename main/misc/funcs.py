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
        partners_list = '\n'.join([f" - {partner[0]} {partner[1]}" for partner in data['partners']])
        profile_text += f"<em>Срощен с</em>:\n{partners_list}"
    return profile_text


def show_matched_traders(traders: list[tuple[str, str]]) -> str:
    if len(traders) == 0:
        traders_list = "<em>Совпадений не найдено</em>"
    else:
        traders_list = '\n'.join([f'{i + 1}. <em>Трейдер</em> "{trader[1]}" - {trader[0]}'
                                  for i, trader in enumerate(traders)])
    answer_string = f"<strong>Совпадения:</strong>\n" \
                    f"{traders_list}"
    return answer_string


def show_matched_merchants(merchants: list[tuple[str, str, str]]) -> str:
    if len(merchants) == 0:
        merchants_list = "<em>Совпадений не найдено</em>"
    else:
        roles = {"merchant": "Мерчант", "platform": "Площадка"}
        merchants_list = '\n'.join([f'{i + 1}. <em>{roles[merch[0]]}</em> "{merch[1]}" - {merch[2]}'
                                  for i, merch in enumerate(merchants)])
    answer_string = f"<strong>Совпадения:</strong>\n" \
                    f"{merchants_list}"
    return answer_string
