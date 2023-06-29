from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb_main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕Добавить"), KeyboardButton(text="🔍Поиск"), KeyboardButton(text="🤝Совпадения")]
], resize_keyboard=True)

kb_chose_entity = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Мерчант"), KeyboardButton(text="Площадка"), KeyboardButton(text="Трейдер")]
], resize_keyboard=True)
