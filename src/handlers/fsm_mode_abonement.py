import logging
import keyboards.common as kb
import re
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import (
    Text,
    Code,
    Bold,
    Italic,
    as_list,
    as_key_value,
    as_marked_list,
)
from aiogram.utils.deep_linking import create_start_link
from const.states import MainGroup, AbonementGroup
from storage.db_api import Database
from utils.config import config
from const.text import cmd, msg, help, ab_del, re_uuid

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering Abonement mode
@router.message(
    StateFilter(default_state),
    or_f(Command("abonement"), F.text == cmd["abonements"]),
)
async def process_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: entering abonement mode")
    await state.set_state(MainGroup.abonement_mode)
    await message.answer(msg["abonement_main"], reply_markup=kb.get_abonement_kb())


# Help command for Abonement mode
@router.message(StateFilter(MainGroup.abonement_mode), Command("help"))
async def process_abonement_mode_help_command(message: Message) -> None:
    logger.info(f"FSM: abonement mode: help command")
    await message.answer(**as_list(Bold(help["ab_cmd"]), help["ab_cancel"]).as_kwargs())


# Help command for Abonement Control mode
@router.message(StateFilter(AbonementGroup), Command("help"))
async def process_abonement_ctrl_help_command(message: Message) -> None:
    logger.info(f"FSM: abonement control: help command")
    await message.answer(
        **as_list(help["ab_ctrl_cmd"], help["ab_ctrl_cancel"]).as_kwargs(),
    )


# Cancel command for Abonement
@router.message(
    StateFilter(MainGroup.abonement_mode),
    (or_f(Command("cancel"), F.text == cmd["exit"])),
)
async def process_abonement_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info(f"FSM: abonement: cancel command")
    await state.clear()
    await message.answer(
        text=msg["abonement_done"], reply_markup=kb.get_main_kb(user_type)
    )


# Cancel command for Abonement Control mode
@router.message(
    StateFilter(AbonementGroup),
    (or_f(Command("cancel"), F.text == cmd["exit"])),
)
async def process_abonement_op_cancel_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: cancel operation command")
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    await message.answer(msg["ab_ctrl_done"], reply_markup=kb.get_abonement_kb())


#
# List Abonements
#
@router.message(StateFilter(MainGroup.abonement_mode), F.text == cmd["my_abonements"])
async def process_my_abonements_command(
    message: Message, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: list my abonements")
    user = await db.user_by_id(user_id)
    if not user:
        logger.warning(f"FSM: abonement: user {user_id} not found")
        return
    # Find my abonements
    my = await db.abonements_list_by_owner(user)
    my_list = [abonement.name for abonement in my]
    # Find other abonements
    other = await db.abonements_list_by_user(user)
    other_list = [abonement.name for abonement in other]
    # Combine abonements info
    if my_list or other_list:
        await message.answer(
            **as_key_value(msg["ab_list_count"], len(my) + len(other)).as_kwargs(),
            reply_markup=kb.no_keyboard,
        )
        nodes: list[Text] = list()
        if my_list:
            nodes.append(Bold(msg["ab_list_my"]))
            nodes.append(as_marked_list(*my_list, marker="👤 "))
        if other_list:
            nodes.append(Bold(msg["ab_list_other"]))
            nodes.append(as_marked_list(*other_list, marker="👥 "))
        nodes.append(Text(""))
        nodes.append(Text(msg["ab_ctrl_cancel"]))
        # Show abonements list
        await message.answer(
            **as_list(*nodes).as_kwargs(),
            reply_markup=kb.get_abonement_list_kb(my, other),
        )
    else:
        # No abonements found
        await message.answer(msg["ab_list_empty"])


#
# Add Abonement: BEGIN
#
@router.message(StateFilter(MainGroup.abonement_mode), F.text == cmd["new_abonement"])
async def process_add_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: BEGIN new abonement")
    await state.set_state(AbonementGroup.name)
    # Ask Abonement name
    await message.answer(
        **as_list(Bold(msg["ab_new_name"]), msg["ab_new_name_format"]).as_kwargs(),
        reply_markup=kb.no_keyboard,
    )


# Add or Edit Abonement: GOOD name
@router.message(
    StateFilter(AbonementGroup.name),
    F.text,
    or_f(F.text.isprintable(), F.text.isspace()),
)
async def process_good_name_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: GOOD NAME for abonement")
    # Check Abonement name
    name = message.text.strip() if message.text else None
    if not name or not name.isprintable():
        await message.answer(msg["ab_new_wrong_name"])
        return
    # Save Abonement name
    await state.update_data(name=name)
    await state.set_state(AbonementGroup.total_visits)
    # Ask about total visits
    await message.answer(
        **as_list(Bold(msg["ab_new_visits"]), msg["ab_zero_visits"]).as_kwargs(),
    )


# Add or Edit Abonement: WRONG name
@router.message(StateFilter(AbonementGroup.name))
async def process_wrong_name_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG NAME for abonement")
    await message.answer(msg["ab_new_wrong_name"])


# Add or Edit Abonement: GOOD total visits
@router.message(StateFilter(AbonementGroup.total_visits), F.text.isdigit())
async def process_good_visits_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: GOOD total visits for abonement")
    # Check Abonement total visits
    total_visits = int(message.text) if message.text else 0
    max_visits = config["BOT"]["ABONEMENTS"]["VISIT_COUNT_LIMIT"]
    if total_visits > max_visits or total_visits < 0:
        await message.answer(
            **as_list(
                f"{msg['ab_wrong_visits']}: 0..{max_visits}", msg["ab_zero_visits"]
            ).as_kwargs()
        )
        return
    # Save Abonement total visits
    await state.update_data(total_visits=total_visits)
    await state.set_state(AbonementGroup.description)
    # Ask about description
    await message.answer(
        **as_list(Bold(msg["ab_new_descr"]), msg["ab_new_skip_descr"]).as_kwargs()
    )


# Add or Edit Abonement: WRONG total visits
@router.message(StateFilter(AbonementGroup.total_visits))
async def process_wrong_visits_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG TOTAL visits for abonement")
    await message.answer(msg["ab_wrong_visits"])


# Add or Edit Abonement: GOOD description
@router.message(
    StateFilter(AbonementGroup.description),
    or_f(Command("skip"), F.text),
)
async def process_good_description_abonement_command(
    message: Message, state: FSMContext, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: GOOD description for abonement")
    # Save Abonement
    if message.text and message.text == "/skip":
        await state.update_data(description=None)
    elif message.text:
        await state.update_data(description=message.text.strip())
    user = await db.user_by_id(user_id)
    abonement_name = (await state.get_data()).get("name")
    total_visits = (await state.get_data()).get("total_visits")
    description = (await state.get_data()).get("description")
    abonement_id = (await state.get_data()).get("abonement_id")
    if not user or not abonement_name or total_visits is None:
        logger.warning(f"FSM: abonement: user {user_id} not found or wrong state")
        return
    if abonement_id:
        abonement = await db.abonement_edit(
            abonement_id=abonement_id,
            name=abonement_name,
            owner=user,
            total_visits=total_visits,
            description=description,
        )
        if abonement:
            logger.info(f"Updated abonement {abonement.id}")
        else:
            logger.warning(
                f"FSM: abonement: can't update abonement {abonement_id} for user {user_id}"
            )
    else:
        abonement = await db.abonement_create(
            name=abonement_name,
            owner=user,
            total_visits=total_visits,
            description=description,
        )
        if abonement:
            logger.info(f"Created new abonement {abonement.id}")
        else:
            logger.warning("FSM: abonement: can't create new abonement")
    # Reset state to Abonenment mode
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    if not abonement:
        return
    # Show info about Abonement
    key = abonement.token
    if abonement_id:
        # EDITED Abonement info
        await message.answer(
            **as_list(
                msg["ab_edit_done"],
                Bold(abonement.name),
                Italic(abonement.description) if abonement.description else "",
                as_key_value(
                    msg["ab_total_visits"],
                    (
                        abonement.total_visits
                        if abonement.total_visits
                        else Italic(msg["ab_unlim_visits"])
                    ),
                ),
                as_key_value(msg["ab_key"], Code(key)),
            ).as_kwargs()
        )
    else:
        # NEW Abonement info
        await message.answer(
            **as_list(
                msg["ab_new_done"],
                Bold(abonement.name),
                "",
                as_key_value(msg["ab_key"], Code(key)),
                "",
                msg["ab_link"],
                (
                    await create_start_link(bot=message.bot, payload=f"abonement_{key}")
                    if message.bot
                    else Bold(msg["unavailable"])
                ),
            ).as_kwargs()
        )
    await message.answer(msg["abonement_main"], reply_markup=kb.get_abonement_kb())


# Add or Edit Abonement: WRONG description
@router.message(StateFilter(AbonementGroup.description))
async def process_wrong_description_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG description for abonement")
    await message.answer(
        **as_list(msg["ab_new_wrong_descr"], msg["ab_new_skip_descr"]).as_kwargs()
    )


#
# Abonement join: BEGIN
#
@router.message(StateFilter(MainGroup.abonement_mode), F.text == cmd["join_abonement"])
async def process_join_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: BEGIN join abonement")
    await state.set_state(AbonementGroup.join)
    await message.answer(
        **as_list(msg["ab_join_begin"], Bold(msg["ab_join_key"])).as_kwargs(),
        reply_markup=kb.no_keyboard,
    )


# Abonement join: GOOD key
@router.message(StateFilter(AbonementGroup.join), F.text)
async def process_good_key_join_abonement_command(
    message: Message, state: FSMContext, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: GOOD key for join abonement")
    # Check token
    abonement_token = message.text.lower() if message.text else None
    if not abonement_token or not re.search(re_uuid, abonement_token):
        await message.answer(
            **as_list(msg["ab_wrong_key_format"], Bold(msg["uuid_format"])).as_kwargs()
        )
        return
    # Token accepted. Find abonement by token
    await state.update_data(abonement_token=abonement_token)
    await state.update_data(user_id=user_id)
    abonement = await db.abonement_by_token(abonement_token)
    if not abonement:
        await message.answer(msg["ab_join_not_exist"])
        return
    # Abonement found. Check if abonement is active
    if abonement.hidden:
        await message.answer(
            **as_list(msg["ab_join_deleted"], Bold(abonement.name)).as_kwargs()
        )
        return
    # Abonement good. Check user is not owner
    if abonement.owner_id == user_id:
        await message.answer(
            **as_list(msg["ab_join_own"], Bold(abonement.name)).as_kwargs()
        )
        return
    # User ok. Check user is not already in abonement
    abonement_user = await db.abonement_user(user_id=user_id, abonement_id=abonement.id)
    if abonement_user:
        await message.answer(
            **as_list(msg["ab_join_already"], Bold(abonement.name)).as_kwargs()
        )
        return
    # Record unique, ok. Ask to add user to abonement
    await state.update_data(abonement_id=abonement.id)
    await state.set_state(AbonementGroup.accept)
    await message.answer(
        **as_list(msg["ab_join_ask"], Bold(abonement.name)).as_kwargs(),
        reply_markup=kb.yes_no_keyboard,
    )


# Abonement join: WRONG key
@router.message(StateFilter(AbonementGroup.join))
async def process_wrong_key_join_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG key for join abonement")
    await message.answer(
        **as_list(msg["ab_wrong_key_format"], Bold(msg["uuid_format"])).as_kwargs()
    )


# Abonement join: GOOD accept answer
@router.message(StateFilter(AbonementGroup.accept), F.text.in_({"Да", "Нет"}))
async def process_good_accept_join_abonement_command(
    message: Message, state: FSMContext, db: Database
) -> None:
    logger.info(f"FSM: abonement: GOOD accept answer for join abonement")
    data = await state.get_data()
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    if message.text and message.text.lower() == cmd["txt_no"]:
        await message.answer(msg["ab_join_no"], reply_markup=kb.get_abonement_kb())
        return
    # Add user to abonement
    user_id = data.get("user_id")
    abonement_id = data.get("abonement_id")
    abonement_token = data.get("abonement_token")
    if not user_id or not abonement_id or not abonement_token:
        logger.warning(f"FSM: abonement: wrong state")
        return
    await db.abonement_user_add(
        user_id=user_id, abonement_id=abonement_id, abonement_token=abonement_token
    )
    await message.answer(msg["ab_join_ok"], reply_markup=kb.get_abonement_kb())


# Abonement join: WRONG accept answer
@router.message(StateFilter(AbonementGroup.accept))
async def process_wrong_accept_join_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG accept answer for join abonement")
    await message.answer(msg["ab_wrong_yes_no"])


# Abonement delete: got answer
@router.message(StateFilter(AbonementGroup.delete))
async def process_good_delete_abonement_command(
    message: Message, state: FSMContext, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: GOOD delete answer for abonement")
    data = await state.get_data()
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    abonement_id = data.get("abonement_id")
    abonement_key = data.get("abonement_key")
    operation = data.get("operation")
    if message.text and message.text.strip().lower() == cmd["txt_yes"] and abonement_id:
        result = await db.abonement_delete(abonement_id=abonement_id, user_id=user_id)
        await message.answer(
            **ab_del(operation, result, abonement_key).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
        )
    else:
        await message.answer(msg["ab_not_del"], reply_markup=kb.get_abonement_kb())


# Unknown command for Abonement mode and Abonement Control mode
@router.message(
    or_f(StateFilter(MainGroup.abonement_mode), StateFilter(AbonementGroup))
)
async def process_abonement_unknown_command(message: Message) -> None:
    await message.answer(msg["ab_unknown"])
