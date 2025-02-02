from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from utils.config import tables, pictures
from const.text import cmd
from const.groups import groups


# MAIN MENU
def get_main_kb(user_type: list[str] = ["unknown"]) -> ReplyKeyboardMarkup:
    # All possible buttons
    buttons_for_all = [cmd["abonements"]]
    buttons_for_unregistered = [cmd["register"]]
    buttons_for_developer = [cmd["diag"]]
    buttons_for_invite_adm = [cmd["invites"]]
    buttons_for_fst_otm = [cmd["tables"]]
    buttons_for_youtube_adm = [cmd["pictures"]]

    # Get available buttons
    buttons_available = []
    if "unregistered" in user_type:
        buttons_available.extend(buttons_for_unregistered)
    if "developer" in user_type:
        buttons_available.extend(buttons_for_developer)
    if "invite_adm" in user_type:
        buttons_available.extend(buttons_for_invite_adm)
    if "fst_otm" in user_type:
        buttons_available.extend(buttons_for_fst_otm)
    if "youtube_adm" in user_type:
        buttons_available.extend(buttons_for_youtube_adm)
    buttons_available.extend(buttons_for_all)

    # Build keyboard
    buttons: list[KeyboardButton] = []
    for name in buttons_available:
        buttons.append(KeyboardButton(text=name))
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=2)
    kb_markup: ReplyKeyboardMarkup = kb_builder.as_markup(
        one_time_keyboard=True, resize_keyboard=True
    )
    return kb_markup


# INVITES MENU
def invites_kb() -> ReplyKeyboardMarkup:
    buttons: list[KeyboardButton] = []
    buttons.append(KeyboardButton(text=cmd["new_invite"]))
    buttons.append(KeyboardButton(text=cmd["invite_history"]))
    buttons.append(KeyboardButton(text=cmd["exit"]))
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=2)
    kb_markup: ReplyKeyboardMarkup = kb_builder.as_markup(
        one_time_keyboard=True, resize_keyboard=True
    )
    return kb_markup


# INVITES CREATION MENU
def get_new_invite_kb() -> ReplyKeyboardMarkup:
    buttons: list[KeyboardButton] = []
    for _, v in groups.items():
        buttons.append(KeyboardButton(text=v))
    buttons.append(KeyboardButton(text=cmd["exit"]))
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=1)
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
def get_pictures_kb() -> ReplyKeyboardMarkup:
    buttons: list[KeyboardButton] = []
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


# GO TO MAIN KEYBOARD
go_home_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=cmd["exit"])]], resize_keyboard=True
)

# YES-NO KEYBOARD
yes_no_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=cmd["yes"]), KeyboardButton(text=cmd["no"])]],
    resize_keyboard=True,
)

# AGREEMENT KEYBOARD
agreement_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=cmd["agree"]), KeyboardButton(text=cmd["disagree"])]
    ],
    resize_keyboard=True,
)

# GET CONTACT KEYBOARD
get_contact_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=cmd["share_phone"], request_contact=True)]],
    one_time_keyboard=True,
    resize_keyboard=True,
)

# NO KEYBOARD
empty_kb = ReplyKeyboardRemove()
