from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from utils.config import tables


# MAIN MENU
def get_main_kb(user_type: list[str] = ["unknown"]) -> ReplyKeyboardMarkup:
    # In future add here "menu_video", "menu_trans", "menu_fst"
    buttons_name_reg = ["Генератор таблиц", "Диагностика"]
    buttons_name_unreg = ["Диагностика", "Генератор таблиц"]
    if "registered" in user_type:
        buttons_name = buttons_name_reg
    else:
        buttons_name = buttons_name_unreg

    buttons: list[KeyboardButton] = []
    for name in buttons_name:
        buttons.append(KeyboardButton(text=name))
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=2)
    kb_markup: ReplyKeyboardMarkup = kb_builder.as_markup(
        one_time_keyboard=True, resize_keyboard=True
    )
    return kb_markup


# GENERATOR MENU
def get_generator_kb() -> ReplyKeyboardMarkup:
    buttons: list[KeyboardButton] = []
    for table in tables:
        buttons.append(KeyboardButton(text=table["title"]))
    buttons.append(KeyboardButton(text="Все"))
    buttons.append(KeyboardButton(text="Выход"))
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=2)
    kb_markup: ReplyKeyboardMarkup = kb_builder.as_markup(
        one_time_keyboard=True, resize_keyboard=True
    )
    return kb_markup


# GO TO MAIN MENU
go_home_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Главное меню")]], resize_keyboard=True
)

# NO KEYBOARD
no_keyboard = ReplyKeyboardRemove()
