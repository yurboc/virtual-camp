from typing import Optional, Sequence
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from storage.db_schema import TgAbonement
from utils.config import tables


# Abonement Callback factory
class AbonementCallbackFactory(CallbackData, prefix="abonement"):
    id: int
    token: str
    action: str


# MAIN MENU
def get_main_kb(user_type: list[str] = ["unknown"]) -> ReplyKeyboardMarkup:
    # In future add here "menu_video", "menu_trans", "menu_fst"
    buttons_name_reg = ["Генератор таблиц", "Диагностика", "Абонементы"]
    buttons_name_unreg = ["Диагностика", "Генератор таблиц", "Абонементы"]
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


# ABONEMENT MENU
def get_abonement_kb() -> ReplyKeyboardMarkup:
    buttons: list[KeyboardButton] = []
    buttons.append(KeyboardButton(text="Мои абонементы"))
    buttons.append(KeyboardButton(text="Создать новый абонемент"))
    buttons.append(KeyboardButton(text="Присоединиться к абонементу"))
    buttons.append(KeyboardButton(text="Выход"))
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=2)
    kb_markup: ReplyKeyboardMarkup = kb_builder.as_markup(
        one_time_keyboard=False, resize_keyboard=True
    )
    return kb_markup


# ABONEMENT LIST MENU
def get_abonement_list_kb(
    my_abonements: Sequence[TgAbonement], other_abonements: Sequence[TgAbonement]
) -> Optional[InlineKeyboardMarkup]:
    if not my_abonements and not other_abonements:
        return None
    builder = InlineKeyboardBuilder()
    for abonement in my_abonements:
        builder.button(
            text=abonement.name,
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="open"
            ),
        )
    for abonement in other_abonements:
        builder.button(
            text=abonement.name,
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="open"
            ),
        )
    builder.adjust(1)
    return builder.as_markup()


# ABONEMENT CONTROL MENU
def get_abonement_control_kb(
    abonement: TgAbonement, user_id: int
) -> Optional[InlineKeyboardMarkup]:
    if not abonement:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(
        text=(
            "Записать посещение" if abonement.total_passes == 0 else "Списать посещение"
        ),
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="pass"
        ),
    )
    builder.button(
        text="История",
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="history"
        ),
    )
    builder.button(
        text="Поделиться",
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="share"
        ),
    )
    if abonement.owner_id == user_id:
        builder.button(
            text="Изменить",
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="edit"
            ),
        )
        builder.button(
            text="Удалить",
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="delete"
            ),
        )
    else:
        builder.button(
            text="Отвязать",
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="delete"
            ),
        )
    builder.button(
        text="Выход",
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="exit"
        ),
    )
    builder.adjust(*[2, 3, 1], repeat=False)
    return builder.as_markup()


# ABONEMENT HISTORY MENU
def get_abonement_history_kb(
    abonement: TgAbonement, offset: int = 0, limit: int = 0, total: int = 0
) -> Optional[InlineKeyboardMarkup]:
    if not abonement:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Назад",
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="open"
        ),
    )
    if offset > 0:
        builder.button(
            text="⬅️",
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="prev"
            ),
        )
    if offset + limit < total:
        builder.button(
            text="➡️",
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="next"
            ),
        )
    builder.button(
        text="Выход",
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="exit"
        ),
    )
    builder.adjust(4)
    return builder.as_markup()


# GO TO MAIN KEYBOARD
go_home_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Главное меню")]], resize_keyboard=True
)

# YES-NO KEYBOARD
yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
    resize_keyboard=True,
)

# NO KEYBOARD
no_keyboard = ReplyKeyboardRemove()
