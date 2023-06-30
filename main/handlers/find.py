from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from ..database import DataBase
from ..keyboards import kb_chose_find, ikb_choose_profile, ikb_profile_find
from ..misc import format_country, show_profile_db


class Find(StatesGroup):
    choose_type = State()
    input_country = State()
    input_username = State()
    show_profile = State()
    edit_profile = State()


find = Router()


@find.message(F.text == "🔍Поиск")
async def find_entity(message: Message, state: FSMContext):
    await state.set_state(Find.choose_type)
    await message.answer("Выберите, что нужно найти", reply_markup=kb_chose_find)


@find.message(Find.choose_type)
async def choose_find_type(messsage: Message, state: FSMContext):
    if messsage.text == "Поиск по юзернейму":
        await state.set_state(Find.input_username)
    else:
        types = {"Трафик": "merchant", "Инструмент": "trader"}
        await state.set_state(Find.input_country)
        await state.update_data(type=types[messsage.text])
        await messsage.answer("Введите страну, по которой будет произведен поиск",
                              reply_markup=ReplyKeyboardRemove())


@find.message(Find.input_country)
async def find_performer(message: Message, state: FSMContext, db: DataBase):
    country = format_country(message.text)
    data = await state.get_data()
    if data['type'] == "merchant":
        types = {"merchant": "Мерчант", "platform": "Площадка"}
        merchants = await db.merchants_by_country(country)
        await state.update_data(merchants=merchants)
        answer_string = '\n'.join([f'{i+1}. <em>{types[merch[0]]}</em> "{merch[1]}"' for i, merch in enumerate(merchants)])
    else:
        traders = await db.traders_by_country(country)
        await state.update_data(traders=traders)
        answer_string = '\n'.join([f'{i+1}. <em>Трейдер</em> "{trader}"' for i, trader in enumerate(traders)])
    await message.answer("<strong>Результаты поиска:</strong>\n" + answer_string,
                         parse_mode='HTML', reply_markup=ikb_choose_profile)


@find.callback_query(F.data == "choose_profile")
async def choose_profile(call: CallbackQuery, state: FSMContext):
    await state.set_state(Find.show_profile)
    await call.message.answer("Введите номер профиля, который хотите просмотреть")
    await call.answer()


@find.message(Find.show_profile)
async def show_profile(message: Message, state: FSMContext, db: DataBase):
    index = int(message.text)
    data = await state.get_data()
    if data['type'] == "merchant":
        name = data['merchants'][index - 1][1]
        person_id = await db.get_merchant_id(name)
        data = await db.get_merchant_data(person_id)
    else:
        name = data['traders'][index - 1]
        person_id = await db.get_trader_id(name)
        data = await db.get_trader_data(person_id)
    await state.set_data(data)
    await state.update_data(persn_id=person_id)
    await message.answer(show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)
