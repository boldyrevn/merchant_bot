from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ikb_countries = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить страны", callback_data="add_countries"),
     InlineKeyboardButton(text="Удалить страны", callback_data="delete_countries")],
    [InlineKeyboardButton(text="Далее", callback_data="goto_input_name")]
])
