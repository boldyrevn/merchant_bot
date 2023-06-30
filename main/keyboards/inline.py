from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ikb_countries = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить страны", callback_data="add_countries"),
     InlineKeyboardButton(text="Удалить страны", callback_data="delete_countries")],
    [InlineKeyboardButton(text="Далее", callback_data="goto_input_name")]
])

ikb_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Изменить имя", callback_data="change_name"),
     InlineKeyboardButton(text="Изменить юзернейм", callback_data="change_username")],
    [InlineKeyboardButton(text="Изменить страны", callback_data="change_countries"),
     InlineKeyboardButton(text="Изменить описание", callback_data="change_description")],
    [InlineKeyboardButton(text="Сохранить профиль", callback_data="save_profile")]
])
