import asyncpg
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from ..database import DataBase
from ..keyboards import kb_chose_find, kb_main_menu,\
    ikb_choose_profile, ikb_profile_find, ikb_profile, ikb_you_sure, ikb_show_matches, ikb_profile_find_change
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
        await messsage.answer("Введите юзернейм, по которому будет произведен поиск",
                              reply_markup=ReplyKeyboardRemove())
        await state.set_state(Find.input_username)
    else:
        types = {"Мерчант/площадка": "merchant", "Трейдер": "trader"}
        try:
            await state.update_data(type=types[messsage.text])
        except KeyError:
            return
        await state.set_state(Find.input_country)
        await messsage.answer("Введите страну, по которой будет произведен поиск",
                              reply_markup=ReplyKeyboardRemove())


@find.message(Find.input_username)
async def search_by_username(message: Message, state: FSMContext, db: DataBase):
    username = message.text.strip()
    result = await db.search_by_username(username)
    if result[0] is None:
        await message.answer("Неверный юзернейм, введите его заново или вернитесь в главное меню с помощью команды "
                             "/reset")
        return
    if result[1] == "merchant":
        data = await db.get_merchant_data(result[0])
    else:
        data = await db.get_trader_data(result[0])
    await state.set_data(data)
    await state.set_state(Find.show_profile)
    await message.answer(show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)


@find.message(Find.input_country)
async def find_performer(message: Message, state: FSMContext, db: DataBase):
    country = format_country(message.text)
    data = await state.get_data()
    try:
        if data['type'] == "merchant" or data['type'] == "platform":
            types = {"merchant": "Мерчант", "platform": "Площадка"}
            merchants = await db.merchants_by_country(country)
            assert len(merchants) > 0
            await state.update_data(merchants=merchants)
            answer_string = '\n'.join([f'{i+1}. <em>{types[merch[0]]}</em> "{merch[1]}"'
                                       for i, merch in enumerate(merchants)])
        else:
            traders = await db.traders_by_country(country)
            assert len(traders) > 0
            await state.update_data(traders=traders)
            answer_string = '\n'.join([f'{i+1}. <em>Трейдер</em> "{trader}"' for i, trader in enumerate(traders)])
    except AssertionError:
        await message.answer("<strong>Поиск не дал результатов.</strong>\n"
                             "Введите другую страну или вернитесь в главное меню с помощью команды /reset",
                             parse_mode="HTML")
        return
    await state.set_state(Find.input_profile_num)
    await message.answer("<strong>Результаты поиска:</strong>\n" + answer_string,
                         parse_mode='HTML', reply_markup=ikb_choose_profile)


@find.callback_query(F.data == "choose_profile", Find.input_profile_num)
async def choose_profile(call: CallbackQuery, state: FSMContext):
    await state.set_state(Find.input_profile_num)
    await call.message.answer("Введите номер профиля, который хотите просмотреть")
    await call.answer()


@find.message(Find.input_profile_num)
async def show_profile(message: Message, state: FSMContext, db: DataBase):
    try:
        index = int(message.text)
        data = await state.get_data()
        if data['type'] == "merchant" or data['type'] == "platform":
            assert 1 <= index <= len(data['merchants'])
            name = data['merchants'][index - 1][1]
            person_id = await db.get_merchant_id(name)
            data = await db.get_merchant_data(person_id)
        else:
            assert 1 <= index <= len(data['traders'])
            name = data['traders'][index - 1]
            person_id = await db.get_trader_id(name)
            data = await db.get_trader_data(person_id)
    except ValueError:
        await message.answer("Значение не является числом, введите номер профиля заново")
        return
    except AssertionError:
        await message.answer("Вы ввели некорректное число, введите номер профиля заново")
        return
    await state.set_data(data)
    await state.set_state(Find.show_profile)
    await message.answer(show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)


@find.callback_query(F.data == "delete_profile", Find.show_profile)
async def are_you_sure(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data['partner_id'] is not None:
        await call.answer(f"Вы не можете удалить профиль, пока он с кем-либо срощен")
        return
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
    await call.message.edit_reply_markup(reply_markup=ikb_profile_find_change)
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
    await message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find_change)


@find.callback_query(F.data == "change_username", Find.edit_profile)
async def call_change_username(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите новый юзернейм")
    await state.set_state(Find.edit_username)
    await call.answer()


@find.message(Find.edit_username)
async def change_username(message: Message, state: FSMContext):
    username = message.text.strip()
    try:
        assert username[0] == '@'
        assert ' ' not in username
    except AssertionError:
        await message.answer("Неправильный формат ввода, введите юзернейм в виде @username")
        return
    await state.update_data(username=username)
    await state.set_state(Find.edit_profile)
    data = await state.get_data()
    await message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find_change)


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
    await message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find_change)


@find.callback_query(F.data == "change_countries", Find.edit_profile)
async def call_change_countries(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data['partner_id'] is not None:
        await call.answer("Вы не можете изменить список стран, пока профиль с кем-либо срощен")
        return
    await call.message.answer("Введите новый список стран через запятую")
    await state.set_state(Find.edit_countries)
    await call.answer()


@find.message(Find.edit_countries)
async def change_countries(message: Message, state: FSMContext, country_list: list[str]):
    try:
        countries = [format_country(country) for country in message.text.split(sep=',')]
        for country in countries:
            assert country in country_list, country
    except IndexError:
        await message.answer("Вводите страны строго через одну запятую")
        return
    except AssertionError as e:
        await message.answer(f'Вы неправильно ввели название одной из стран: "{e}"')
        return
    await state.update_data(countries=countries)
    await state.set_state(Find.edit_profile)
    data = await state.get_data()
    await message.answer(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find_change)


@find.callback_query(F.data == "save_profile", Find.edit_profile)
async def save_profile(call: CallbackQuery, state: FSMContext, db: DataBase):
    data = await state.get_data()
    try:
        if data['type'] == 'trader':
            await db.update_trader(data)
        else:
            await db.update_merchant(data)
    except asyncpg.exceptions.PostgresSyntaxError:
        await call.message.answer("Не используйте в имени и описании одинарные ковычки")
        await call.answer()
        return
    await state.set_state(Find.show_profile)
    await call.message.edit_text(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)
    await call.answer("Профиль сохранен")


@find.callback_query(F.data == "discard_changes", Find.edit_profile)
async def discard_changes(call: CallbackQuery, state: FSMContext, db: DataBase):
    data = await state.get_data()
    if data['type'] == "trader":
        data = await db.get_trader_data(data['id'])
    else:
        data = await db.get_merchant_data(data['id'])
    await state.set_data(data)
    await state.set_state(Find.show_profile)
    await call.message.edit_text(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)
    await call.answer("Изменения отменены")


@find.callback_query(F.data == "find_matches", Find.show_profile)
async def find_matches(call: CallbackQuery, state: FSMContext, db: DataBase):
    data = await state.get_data()
    partner_id = data.get('partner_id', None)
    try:
        if data['type'] == "trader":
            matched_merchants = await db.find_trader_matches(data['id'], partner_id)
            assert len(matched_merchants) > 0
            await state.update_data(matched_merchants=matched_merchants)
            await call.message.answer(text=show_matched_merchants(matched_merchants), parse_mode="HTML",
                                      reply_markup=ikb_show_matches)
        else:
            matched_traders = await db.find_merchant_matches(data['id'], partner_id)
            assert len(matched_traders) > 0
            await state.update_data(matched_traders=matched_traders)
            await call.message.answer(text=show_matched_traders(matched_traders), parse_mode="HTML",
                                      reply_markup=ikb_show_matches)
    except AssertionError:
        await call.answer("Совпадений не найдено")
        return
    await state.set_state(Find.show_matches)
    await call.answer()


@find.callback_query(F.data == "back_to_search", Find.show_profile)
async def back_to_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(Find.input_country)
    await call.message.answer("Введите страну, по которой будет произведен поиск")
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
    try:
        index = int(message.text)
        data = await state.get_data()
        if data['type'] == "trader":
            assert 1 <= index <= len(data['matched_merchants'])
            name = data['matched_merchants'][index - 1][1]
            country = data['matched_merchants'][index - 1][2]
            trader_id = data['id']
            merchant_id = await db.get_merchant_id(name)
        else:
            assert 1 <= index <= len(data['matched_traders'])
            name = data['matched_traders'][index - 1][0]
            country = data['matched_traders'][index - 1][1]
            merchant_id = data['id']
            trader_id = await db.get_trader_id(name)
    except ValueError:
        await message.answer("Значение не является числом, введите номер профиля заново")
        return
    except AssertionError:
        await message.answer("Вы ввели некорректное число, введите номер профиля заново")
        return
    await db.add_match(merchant_id, trader_id, country)
    if data['type'] == "trader":
        new_data = await db.get_trader_data(data['id'])
    else:
        new_data = await db.get_merchant_data(data['id'])
    await state.set_data(new_data)
    await state.set_state(Find.show_profile)
    await message.answer(text=show_profile_db(new_data), parse_mode="HTML", reply_markup=ikb_profile_find)


@find.callback_query(F.data == "delete_match", Find.show_profile)
async def input_delete_match(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if len(data['merged_countries']) == 0:
        await call.answer("Профиль ни с кем не срощен")
        return
    await state.set_state(Find.delete_match)
    await call.message.answer("Введите название страны, по которой хотите отменить сращивание")
    await call.answer()


@find.message(Find.delete_match)
async def delete_match(message: Message, state: FSMContext, db: DataBase):
    data = await state.get_data()
    country = message.text.strip()
    if country not in data['merged_countries']:
        await message.answer("Такой страны нет в списке, введите название заново")
        return
    if data['type'] == "trader":
        merchant_id = data['partner_id']
        trader_id = data['id']
        await db.delete_match_country(merchant_id, trader_id, country)
    else:
        merchant_id = data['id']
        trader_id = data['partner_id']
        await db.delete_match_country(merchant_id, trader_id, country)
    if len(data['merged_countries']) == 1:
        await db.delete_match(merchant_id, trader_id)
    new_data = await db.get_trader_data(data['id'])
    await state.set_data(new_data)
    await state.set_state(Find.show_profile)
    await message.answer(text=show_profile_db(new_data), parse_mode="HTML", reply_markup=ikb_profile_find)


@find.callback_query(F.data == "turn_on_search", Find.show_profile)
async def turn_on_search(call: CallbackQuery, state: FSMContext, db: DataBase):
    data = await state.get_data()
    data['in_search'] = not data['in_search']
    await state.update_data(in_search=data['in_search'])
    if data['type'] == "trader":
        await db.trader_in_search(data['in_search'], data['id'])
    else:
        await db.merchant_in_search(data['in_search'], data['id'])
    await call.message.edit_text(text=show_profile_db(data), parse_mode="HTML", reply_markup=ikb_profile_find)
    await call.answer()


