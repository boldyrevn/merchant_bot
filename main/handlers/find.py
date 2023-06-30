from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from ..keyboards import kb_chose_find
from ..database import DataBase
from ..misc import format_country


class Find(StatesGroup):
    choose_type = State()
    input_country = State()
    input_username = State()
    show_profile = State()


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
        answer_string = '\n'.join([f'- <em>{types[merchant[0]]}</em> "{merchant[1]}"' for merchant in merchants])
    else:
        traders = await db.traders_by_country(country)
        answer_string = '\n'.join([f'- <em>Трейдер</em> "{trader}"' for trader in traders])
    await message.answer("<strong>Результаты поиска:</strong>\n" + answer_string,
                         parse_mode='HTML')

