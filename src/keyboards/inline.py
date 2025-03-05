from typing import Optional, Sequence
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from storage.db_schema import TgAbonement, TgAbonementVisit
from const.text import cmd
from const.formats import date_h_m_fmt


# Abonement Callback factory
class AbonementCallbackFactory(CallbackData, prefix="abonement"):
    id: int
    token: str
    action: str


# ABONEMENT LIST MENU for TgAbonement items
def get_abonement_items_kb(
    abonements: list[TgAbonement],
) -> Optional[InlineKeyboardMarkup]:
    if not abonements:
        return None
    builder = InlineKeyboardBuilder()
    for abonement in abonements:
        builder.button(
            text=abonement.name,
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="open"
            ),
        )
    builder.adjust(1)
    return builder.as_markup()


# ABONEMENT LIST MENU
def get_abonement_list_kb(
    my_abonements: Sequence[TgAbonement], other_abonements: Sequence[TgAbonement]
) -> Optional[InlineKeyboardMarkup]:
    abonements = []
    for abonement in my_abonements:
        abonements.append(abonement)
    for abonement in other_abonements:
        abonements.append(abonement)
    return get_abonement_items_kb(abonements)


# ABONEMENT CONTROL MENU
def get_abonement_control_kb(
    abonement: TgAbonement, user_id: int, notify: Optional[str]
) -> Optional[InlineKeyboardMarkup]:
    if not abonement:
        return None
    builder = InlineKeyboardBuilder()
    # Visit Button
    builder.button(
        text=(cmd["plus_visit"] if abonement.total_visits == 0 else cmd["minus_visit"]),
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="ask_visit"
        ),
    )
    # History Button
    builder.button(
        text=cmd["visits_history"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="history"
        ),
    )
    # Share Button
    builder.button(
        text=cmd["share"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="share"
        ),
    )
    if abonement.owner_id == user_id:
        # Edit Button
        second_line_buttons_cnt = 3
        builder.button(
            text=cmd["edit"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="edit"
            ),
        )
        # Delete Button
        builder.button(
            text=cmd["delete"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="delete"
            ),
        )
    else:
        # Unlink Button
        second_line_buttons_cnt = 2
        builder.button(
            text=cmd["unlink"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="delete"
            ),
        )
    if notify and notify == "all":
        # Notify ON Button
        builder.button(
            text=cmd["notify_on"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="notify_off"
            ),
        )
    else:
        # Notify OFF Button
        builder.button(
            text=cmd["notify_off"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="notify_on"
            ),
        )
    # Exit Button
    builder.button(
        text=cmd["exit"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="exit"
        ),
    )
    # Adjust buttons
    builder.adjust(*[2, second_line_buttons_cnt, 2], repeat=False)
    return builder.as_markup()


# ABONEMENT HISTORY MENU
def get_abonement_history_kb(
    abonement: TgAbonement, offset: int = 0, limit: int = 0, total: int = 0
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if total:
        # Edit Button
        builder.button(
            text=cmd["edit"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="visit_edit"
            ),
        )
        # Remove Button
        builder.button(
            text=cmd["delete"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="visit_delete"
            ),
        )
    # Back Button
    builder.button(
        text=cmd["back"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="open"
        ),
    )
    if offset > 0:
        # Prev Button
        builder.button(
            text=cmd["prev"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="prev"
            ),
        )
    if offset + limit < total:
        # Next Button
        builder.button(
            text=cmd["next"],
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token=abonement.token, action="next"
            ),
        )
    # Exit Button
    builder.button(
        text=cmd["exit"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="exit"
        ),
    )
    # Adjust buttons
    builder.adjust(*[2, 4], repeat=False)
    return builder.as_markup()


# ABONEMENT VISITS EDIT/DELETE MENU
def get_abonement_visits_kb(
    abonement: TgAbonement, visits_list: Sequence[TgAbonementVisit], action: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for visit in visits_list:
        # Edit/Delete Button
        builder.button(
            text=visit.ts.strftime(date_h_m_fmt),
            callback_data=AbonementCallbackFactory(
                id=abonement.id, token="", action="{}_{}".format(action, visit.id)
            ),
        )
    # Exit Button
    builder.button(
        text=cmd["exit"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="exit"
        ),
    )
    # Adjust buttons
    builder.adjust(1)
    return builder.as_markup()


# ABONEMENT YES-NO KEYBOARD
def get_abonement_yes_no_kb(abonement: TgAbonement) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=cmd["yes"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="yes"
        ),
    )
    builder.button(
        text=cmd["no"],
        callback_data=AbonementCallbackFactory(
            id=abonement.id, token=abonement.token, action="no"
        ),
    )
    builder.adjust(2)
    return builder.as_markup()
