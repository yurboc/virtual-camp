from typing import Optional, Sequence
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from storage.db_schema import TgAbonement
from utils.config import tables, pictures
from const.text import cmd


# Abonement Callback factory
class AbonementCallbackFactory(CallbackData, prefix="abonement"):
    id: int
    token: str
    action: str


# MAIN MENU
def get_main_kb(user_type: list[str] = ["unknown"]) -> ReplyKeyboardMarkup:
    buttons_name_reg = [cmd["diag"], cmd["tables"], cmd["abonements"], cmd["pictures"]]
    buttons_name_unreg = [cmd["register"]] + buttons_name_reg
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
    buttons.append(KeyboardButton(text=cmd["all"]))
    buttons.append(KeyboardButton(text=cmd["exit"]))
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=2)
    kb_markup: ReplyKeyboardMarkup = kb_builder.as_markup(
        one_time_keyboard=True, resize_keyboard=True
    )
    return kb_markup


# PICTURES MENU
def get_pictures_kb(select_mode: bool) -> ReplyKeyboardMarkup:
    buttons: list[KeyboardButton] = []
    if select_mode:
        buttons.append(KeyboardButton(text=cmd["as_picture"]))
        buttons.append(KeyboardButton(text=cmd["as_document"]))
    for picture in pictures:
        buttons.append(KeyboardButton(text=picture["title"]))
    buttons.append(KeyboardButton(text=cmd["exit"]))
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=2)
    kb_markup: ReplyKeyboardMarkup = kb_builder.as_markup(
        one_time_keyboard=True, resize_keyboard=True
    )
    return kb_markup


# ABONEMENT MENU
def get_abonement_kb() -> ReplyKeyboardMarkup:
    buttons: list[KeyboardButton] = []
    buttons.append(KeyboardButton(text=cmd["my_abonements"]))
    buttons.append(KeyboardButton(text=cmd["new_abonement"]))
    buttons.append(KeyboardButton(text=cmd["join_abonement"]))
    buttons.append(KeyboardButton(text=cmd["exit"]))
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
        text=(cmd["plus_visit"] if abonement.total_visits == 0 else cmd["minus_visit"]),
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="visit"
        ),
    )
    builder.button(
        text=cmd["visits_history"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="history"
        ),
    )
    builder.button(
        text=cmd["share"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="share"
        ),
    )
    if abonement.owner_id == user_id:
        builder.button(
            text=cmd["edit"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="edit"
            ),
        )
        builder.button(
            text=cmd["delete"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="delete"
            ),
        )
    else:
        builder.button(
            text=cmd["unlink"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="delete"
            ),
        )
    builder.button(
        text=cmd["exit"],
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
        text=cmd["back"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="open"
        ),
    )
    if offset > 0:
        builder.button(
            text=cmd["prev"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="prev"
            ),
        )
    if offset + limit < total:
        builder.button(
            text=cmd["next"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="next"
            ),
        )
    builder.button(
        text=cmd["exit"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="exit"
        ),
    )
    builder.adjust(4)
    return builder.as_markup()


# GO TO MAIN KEYBOARD
go_home_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=cmd["go_home"])]], resize_keyboard=True
)

# YES-NO KEYBOARD
yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=cmd["yes"]), KeyboardButton(text=cmd["no"])]],
    resize_keyboard=True,
)

# AGREEMENT KEYBOARD
agreement_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=cmd["agree"]), KeyboardButton(text=cmd["disagree"])]
    ],
    resize_keyboard=True,
)

# GET CONTACT KEYBOARD
get_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=cmd["share_phone"], request_contact=True)]],
    one_time_keyboard=True,
    resize_keyboard=True,
)

# NO KEYBOARD
no_keyboard = ReplyKeyboardRemove()
