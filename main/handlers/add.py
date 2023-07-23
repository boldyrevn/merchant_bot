import asyncpg
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from ..database import DataBase
from ..keyboards import kb_chose_entity, kb_main_menu, ikb_countries, ikb_profile
from ..misc import format_country, show_profile


class Add(StatesGroup):
    choose_type = State()
    input_country = State()
    delete_country = State()
    add_country = State()
    input_name = State()
    input_username = State()
    input_description = State()
    show_result = State()


add = Router()


@add.message(F.text == "➕Добавить")
async def add_entity(message: Message, state: FSMContext):
    await state.set_state(Add.choose_type)
    await state.update_data(profile_is_ready=False)
    await message.answer("Выберите, кого вы хотите добавить", reply_markup=kb_chose_entity)


@add.message(Add.choose_type)
async def choose_type(message: Message, state: FSMContext):
    types = {"Мерчант": "merchant", "Площадка": "platform", "Трейдер": "trader"}
    await state.update_data(type=types[message.text])
    await state.set_state(Add.input_country)
    await message.answer(text="Введите через запятую страны, в которых есть трафик",
                         reply_markup=ReplyKeyboardRemove())


@add.message(Add.input_country)
async def set_countries(message: Message, state: FSMContext, country_list: list[str]):
    try:
        countries = [format_country(country) for country in message.text.split(sep=',')]
        for country in countries:
            assert country in country_list, country
    except IndexError:
        await message.answer("Вводите страны строго через запятую")
        return
    except AssertionError as e:
        await message.answer(f'Вы неправильно ввели название одной из стран: "{e}"')
        return
    await state.update_data(countries=countries)
    answer_string = '\n'.join([f'▪ {country}' for country in countries])
    await message.answer(text="Трафик есть в следующих странах:\n" + answer_string,
                         reply_markup=ikb_countries)


@add.callback_query(F.data == "add_countries", Add.input_country)
async def add_countries(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.add_country)
    await call.message.answer("Введите через запятую страны, которые хотите добавить")
    await call.answer()


@add.message(Add.add_country)
async def add_countries(message: Message, state: FSMContext, country_list: list[str]):
    try:
        new_countries: list = [format_country(country) for country in message.text.split(sep=',')]
        for country in new_countries:
            assert country in country_list, country
    except IndexError:
        await message.answer("Вводите страны строго через запятую")
        return
    except AssertionError as e:
        await message.answer(f'Вы неправильно ввели название одной из стран: "{e}"')
        return
    await state.set_state(Add.input_country)
    countries: list = (await state.get_data())['countries']
    countries.extend(new_countries)
    await state.update_data(countries=countries)
    answer_string = '\n'.join([f'▪ {country}' for country in countries])
    await message.answer(text="Трафик есть в следующих странах:\n" + answer_string,
                         reply_markup=ikb_countries)


@add.callback_query(F.data == "delete_countries", Add.input_country)
async def delete_countries(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.delete_country)
    await call.message.answer("Введите через запятую страны, которые хотите удалить")
    await call.answer()


@add.message(Add.delete_country)
async def delete_country(message: Message, state: FSMContext):
    try:
        del_countries: list = [format_country(country) for country in message.text.split(sep=',')]
    except IndexError:
        await message.answer("Вводите страны строго через одну запятую")
        return
    countries: list = (await state.get_data())['countries']
    for country in del_countries:
        try:
            countries.remove(country)
        except ValueError:
            pass
    await state.update_data(countries=countries)
    await state.set_state(Add.input_country)
    answer_string = '\n'.join([f'▪ {country}' for country in countries])
    await message.answer(text="Трафик есть в следующих странах:\n" + answer_string,
                         reply_markup=ikb_countries)


@add.callback_query(F.data == "goto_input_name", Add.input_country)
async def invite_input_name(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data['profile_is_ready']:
        await call.message.answer(text=show_profile(data), parse_mode="HTML", reply_markup=ikb_profile)
        await state.set_state(Add.show_result)
        await call.answer()
    else:
        await state.set_state(Add.input_name)
        await call.message.answer("Введите имя, которое будет отображаться при поиске")
        await call.answer()


@add.message(Add.input_name)
async def input_name(message: Message, state: FSMContext, db: DataBase):
    name = message.text.strip()
    await state.update_data(name=name)
    data = await state.get_data()
    if data['profile_is_ready']:
        await message.answer(text=show_profile(data), parse_mode="HTML", reply_markup=ikb_profile)
        await state.set_state(Add.show_result)
    else:
        if data['type'] == 'trader' and await db.name_in_traders(name):
            await message.answer("Трейдер с таким именем уже существует, введите другое имя")
            return
        elif data['type'] != 'trader' and await db.name_in_merchants(name):
            await message.answer("Мерчант с таким именем уже существует, введите другое имя")
            return
        await message.answer("Введите юзернейм телеграм в формате @username")
        await state.set_state(Add.input_username)


@add.message(Add.input_username)
async def input_username(message: Message, state: FSMContext, db: DataBase):
    username = message.text.strip()
    try:
        assert username[0] == '@'
        assert ' ' not in username
    except AssertionError:
        await message.answer("Неправильный формат ввода, введите юзернейм в виде @username")
        return
    await state.update_data(username=username)
    data = await state.get_data()
    if data['profile_is_ready']:
        await message.answer(text=show_profile(data), parse_mode="HTML", reply_markup=ikb_profile)
        await state.set_state(Add.show_result)
    else:
        if data['type'] == 'trader' and await db.username_in_traders(username):
            await message.answer("Трейдер с таким юзернеймом уже существует, введите другой юзернейм")
            return
        elif data['type'] != 'trader' and await db.username_in_merchants(username):
            await message.answer("Мерчант с таким юзернеймом уже существует, введите другой юзернейм")
            return
        await message.answer("Введите описание")
        await state.set_state(Add.input_description)


@add.message(Add.input_description)
async def input_description(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description,
                            profile_is_ready=True,
                            admin_username=message.from_user.username)
    await state.set_state(Add.show_result)
    data = await state.get_data()
    await message.answer(text=show_profile(data), parse_mode="HTML", reply_markup=ikb_profile)


@add.callback_query(F.data == "change_name", Add.show_result)
async def change_name(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.input_name)
    await call.message.answer("Введите новое имя")
    await call.answer()


@add.callback_query(F.data == "change_username", Add.show_result)
async def change_username(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.input_username)
    await call.message.answer("Введите новый юзернейм")
    await call.answer()


@add.callback_query(F.data == "change_description", Add.show_result)
async def change_description(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.input_description)
    await call.message.answer("Введите новое описание")
    await call.answer()


@add.callback_query(F.data == "change_countries", Add.show_result)
async def change_countries(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.input_country)
    countries: list = (await state.get_data())['countries']
    answer_string = '\n'.join([f'▪ {country}' for country in countries])
    await call.message.answer(text="Трафик есть в следующих странах:\n" + answer_string,
                              reply_markup=ikb_countries)
    await call.answer()


@add.callback_query(F.data == "save_profile", Add.show_result)
async def save_profile(call: CallbackQuery, state: FSMContext, db: DataBase):
    data = await state.get_data()
    try:
        if data['type'] == 'trader':
            await db.add_trader(data)
        else:
            await db.add_merchant(data)
    except asyncpg.exceptions.PostgresSyntaxError:
        await call.message.answer("Не используйте в имени и описании одинарные ковычки")
        await call.message.answer(text=show_profile(data), parse_mode="HTML", reply_markup=ikb_profile)
        await call.answer()
        return
    await call.message.answer("Данные успешно сохранены", reply_markup=kb_main_menu)
    await state.clear()
    await call.answer()

