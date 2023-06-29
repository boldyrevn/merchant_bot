from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from ..keyboards import kb_chose_entity, ikb_countries
from ..misc import format_country


class Add(StatesGroup):
    choose_type = State()
    input_country = State()
    delete_country = State()
    add_country = State()
    input_name = State()
    input_username = State()
    input_description = State()
    show_result = State()
    save_result = State()


add = Router()


@add.message(F.text == "➕Добавить")
async def add_entity(message: Message, state: FSMContext):
    await state.set_state(Add.choose_type)
    await message.answer("Выберите, кого вы хотите добавить", reply_markup=kb_chose_entity)


@add.message(Add.choose_type)
async def choose_type(message: Message, state: FSMContext):
    types = {"Мерчант": "merchant", "Площадка": "platform", "Трейдер": "trader"}
    await state.update_data(entity_type=types[message.text])
    await state.set_state(Add.input_country)
    await message.answer(text="Введите через запятую страны, в которых есть трафик",
                         reply_markup=ReplyKeyboardRemove())


@add.message(Add.input_country)
async def set_countries(message: Message, state: FSMContext):
    countries = [format_country(country) for country in message.text.split(sep=',')]
    await state.update_data(countries=countries)
    answer_string = '\n'.join([f'▪ {country}' for country in countries])
    await message.answer(text="Трафик есть в следующих странах:\n" + answer_string,
                         reply_markup=ikb_countries)


@add.callback_query(F.data == "add_countries")
async def add_countries(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.add_country)
    await call.message.answer("Введите через запятую страны, которые хотите добавить")
    await call.answer()


@add.message(Add.add_country)
async def add_countries(message: Message, state: FSMContext):
    await state.set_state(Add.input_country)
    countries: list = (await state.get_data())['countries']
    new_countries: list = [format_country(country) for country in message.text.split(sep=',')]
    countries.extend(new_countries)
    await state.update_data(countries=countries)
    answer_string = '\n'.join([f'▪ {country}' for country in countries])
    await message.answer(text="Трафик есть в следующих странах:\n" + answer_string,
                         reply_markup=ikb_countries)


@add.callback_query(F.data == "delete_countries")
async def delete_countries(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.delete_country)
    await call.message.answer("Введите через запятую страны, которые хотите удалить")
    await call.answer()


@add.message(Add.delete_country)
async def delete_country(message: Message, state: FSMContext):
    await state.set_state(Add.input_country)
    countries: list = (await state.get_data())['countries']
    del_countries: list = [format_country(country) for country in message.text.split(sep=',')]
    for country in del_countries:
        try:
            countries.remove(country)
        except ValueError:
            pass
    await state.update_data(countries=countries)
    answer_string = '\n'.join([f'▪ {country}' for country in countries])
    await message.answer(text="Трафик есть в следующих странах:\n" + answer_string,
                         reply_markup=ikb_countries)


@add.callback_query(F.data == "goto_input_name")
async def invite_input_name(call: CallbackQuery, state: FSMContext):
    await state.set_state(Add.input_name)
    await call.message.answer("Введите имя, которое будет отображаться при поиске")
    await call.answer()


@add.message(Add.input_name)
async def input_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await message.answer("Введите юзернейм телеграм в формате @username")
    await state.set_state(Add.input_username)


@add.message(Add.input_username)
async def input_username(message: Message, state: FSMContext):
    username = message.text.strip()
    await state.update_data(username=username)
    await message.answer("Введите описание")
    await state.set_state(Add.input_description)
