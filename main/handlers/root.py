from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ..database import DataBase
from ..keyboards import kb_main_menu
from ..misc import show_matches

root = Router()


@root.message(Command("start"))
async def start_command(message: Message):
    await message.answer(text=f"{message.from_user.first_name}, выберите действие",
                         reply_markup=kb_main_menu)


@root.message(Command("reset"))
async def reset_command(message: Message, state: FSMContext):
    await message.answer("Все изменения отменены", reply_markup=kb_main_menu)
    await state.clear()


@root.message(F.text == "🤝Совпадения")
async def list_matches(message: Message, db: DataBase):
    matches = await db.get_all_matches()
    await message.answer(text=show_matches(matches), parse_mode="HTML")
