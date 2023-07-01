from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from ..database import DataBase
from ..keyboards import kb_chose_find, kb_main_menu,\
    ikb_choose_profile, ikb_profile_find, ikb_profile, ikb_you_sure, ikb_show_matches
from ..misc import format_country, show_profile_db, show_matched_traders, show_matched_merchants


class Find(StatesGroup):
    choose_type = State()
    input_country = State()
    input_username = State()
    input_profile_num = State()
    show_profile = State()
    edit_profile = State()
    edit_name = State()
    edit_username = State()
    edit_description = State()
    edit_countries = State()
    delete_profile = State()
    show_matches = State()
    make_match = State()
    delete_match = State()


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
    await state.set_state(Find.input_profile_num)
    await call.message.answer("Введите номер профиля, который хотите просмотреть")
    await call.answer()


@find.message(Find.input_profile_num)
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
    await state.set_state(Find.show_profile)
    await state.update_data(persn_id=person_id)
    await message.answer(show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)


@find.callback_query(F.data == "delete_profile")
async def are_you_sure(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Find.delete_profile)
    await call.message.answer(text=f'Вы точно хотите удалить профиль "{data["name"]}"?',
                              reply_markup=ikb_you_sure)
    await call.answer()


@find.callback_query(F.data == "yes", Find.delete_profile)
async def delete_profile(call: CallbackQuery, state: FSMContext, db: DataBase):
    data = await state.get_data()
    if data['type'] == "trader":
        await db.delete_trader(data['id'])
    else:
        await db.delete_merchant(data['id'])
    await call.message.answer("Профиль удален", reply_markup=kb_main_menu)
    await call.answer()
    await state.clear()


@find.callback_query(F.data == "no", Find.delete_profile)
async def not_delete_profile(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Find.show_profile)
    await call.message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)


@find.callback_query(F.data == "edit_profile")
async def change_profile(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=ikb_profile)
    await state.set_state(Find.edit_profile)


@find.callback_query(F.data == "change_name", Find.edit_profile)
async def call_change_name(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите новое имя")
    await state.set_state(Find.edit_name)
    await call.answer()


@find.message(Find.edit_name)
async def change_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(Find.edit_profile)
    data = await state.get_data()
    await message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile)


@find.callback_query(F.data == "change_username", Find.edit_profile)
async def call_change_username(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите новый юзернейм")
    await state.set_state(Find.edit_username)
    await call.answer()


@find.message(Find.edit_username)
async def change_username(message: Message, state: FSMContext):
    username = message.text.strip()
    await state.update_data(username=username)
    await state.set_state(Find.edit_profile)
    data = await state.get_data()
    await message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile)


@find.callback_query(F.data == "change_description", Find.edit_profile)
async def call_change_description(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите новое описание")
    await state.set_state(Find.edit_description)
    await call.answer()


@find.message(Find.edit_description)
async def change_description(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    await state.set_state(Find.edit_profile)
    data = await state.get_data()
    await message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile)


@find.callback_query(F.data == "change_countries", Find.edit_profile)
async def call_change_countries(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите новый список стран через запятую")
    await state.set_state(Find.edit_countries)
    await call.answer()


@find.message(Find.edit_countries)
async def change_countries(message: Message, state: FSMContext):
    countries = [format_country(country) for country in message.text.split(sep=',')]
    await state.update_data(countries=countries)
    await state.set_state(Find.edit_profile)
    data = await state.get_data()
    await message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile)


@find.callback_query(F.data == "save_profile", Find.edit_profile)
async def save_profile(call: CallbackQuery, state: FSMContext, db: DataBase):
    data = await state.get_data()
    if data['type'] == "trader":
        await db.update_trader(data)
    else:
        await db.update_merchant(data)
    await state.set_state(Find.show_profile)
    await call.message.edit_text(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)
    await call.answer("Профиль сохранен")


@find.callback_query(F.data == "find_matches", Find.show_profile)
async def find_matches(call: CallbackQuery, state: FSMContext, db: DataBase):
    data = await state.get_data()
    await state.set_state(Find.show_matches)
    if data['type'] == "trader":
        matched_merchants = await db.find_trader_matches(data['id'])
        await state.update_data(matched_merchants=matched_merchants)
        await call.message.answer(text=show_matched_merchants(matched_merchants), parse_mode="HTML",
                                  reply_markup=ikb_show_matches)
    else:
        matched_traders = await db.find_merchant_matches(data['id'])
        await state.update_data(matched_traders=matched_traders)
        await call.message.answer(text=show_matched_traders(matched_traders), parse_mode="HTML",
                                  reply_markup=ikb_show_matches)
    await call.answer()


@find.callback_query(F.data == "back_to_profile", Find.show_matches)
async def back_to_profile(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Find.show_profile)
    await call.message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)
    await call.answer()


@find.callback_query(F.data == "make_match", Find.show_matches)
async def input_match_num(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Find.make_match)
    await call.message.answer(f'Введите номер профиля из списка, с которым хотите сростить "{data["name"]}"')
    await call.answer()


@find.message(Find.make_match)
async def make_match(message: Message, state: FSMContext, db: DataBase):
    index = int(message.text)
    data = await state.get_data()
    if data['type'] == "trader":
        name = data['matched_merchants'][index - 1][1]
        trader_id = data['id']
        merchant_id = await db.get_merchant_id(name)
    else:
        name = data['matched_traders'][index - 1][1]
        merchant_id = data['id']
        trader_id = await db.get_trader_id(name)
    await db.add_match(merchant_id, trader_id)
    if data['type'] == "trader":
        new_data = await db.get_trader_data(data['id'])
    else:
        new_data = await db.get_merchant_data(data['id'])
    await state.set_data(new_data)
    await state.set_state(Find.show_profile)
    await message.answer(text=show_profile_db(new_data), parse_mode="HTML", reply_markup=ikb_profile_find)


@find.callback_query(F.data == "delete_match", Find.show_profile)
async def input_delete_match(call: CallbackQuery, state: FSMContext):
    await state.set_state(Find.delete_match)
    await call.message.answer("Введите имя человека, с которым хотите отменить сращивание")
    await call.answer()


@find.message(Find.delete_match)
async def delete_match(message: Message, state: FSMContext, db: DataBase):
    data = await state.get_data()
    name = message.text.strip()
    if data['type'] == "trader":
        merchant_id = await db.get_merchant_id(name)
        trader_id = data['id']
        await db.delete_match(merchant_id, trader_id)
        new_data = await db.get_trader_data(data['id'])
    else:
        merchant_id = data['id']
        trader_id = await db.get_trader_id(name)
        await db.delete_match(merchant_id, trader_id)
        new_data = await db.get_merchant_data(data['id'])
    await state.set_data(new_data)
    await state.set_state(Find.show_profile)
    await message.answer(text=show_profile_db(new_data), parse_mode="HTML", reply_markup=ikb_profile_find)

