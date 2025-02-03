import logging
import keyboards.reply as kb
import keyboards.inline as ikb
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
from datetime import datetime
from const.states import MainGroup, AbonementGroup
from storage.db_api import Database
from utils.config import config
from modules import queue_publisher
from const.text import cmd, msg, help
from const.formats import re_uuid, date_fmt, date_h_m_fmt
from modules.msg_creator import ab_del

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering Abonement mode
@router.message(
    StateFilter(default_state), or_f(Command("abonement"), F.text == cmd["abonements"])
)
async def process_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info("FSM: abonement: entering abonement mode")
    await state.set_state(MainGroup.abonement_mode)
    await message.answer(msg["abonement_main"], reply_markup=kb.get_abonement_kb())


# Help command for Abonement mode
@router.message(StateFilter(MainGroup.abonement_mode), Command("help"))
async def process_abonement_mode_help_command(message: Message) -> None:
    logger.info("FSM: abonement mode: help command")
    await message.answer(**as_list(Bold(help["ab_cmd"]), help["ab_cancel"]).as_kwargs())


# Help command for Abonement Control mode
@router.message(StateFilter(AbonementGroup), Command("help"))
async def process_abonement_ctrl_help_command(message: Message) -> None:
    logger.info("FSM: abonement control: help command")
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
    logger.info("FSM: abonement: cancel command")
    await state.clear()
    await message.answer(
        text=msg["abonement_done"], reply_markup=kb.get_main_kb(user_type)
    )


# Cancel command for Abonement Control mode
@router.message(
    StateFilter(AbonementGroup), (or_f(Command("cancel"), F.text == cmd["exit"]))
)
async def process_abonement_op_cancel_command(
    message: Message, state: FSMContext
) -> None:
    logger.info("FSM: abonement: cancel operation command")
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
    logger.info("FSM: abonement: list my abonements")
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
            reply_markup=kb.empty_kb,
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
            reply_markup=ikb.get_abonement_list_kb(my, other),
        )
    else:
        # No abonements found
        await message.answer(msg["ab_list_empty"])


#
# Add Abonement: BEGIN
#
@router.message(StateFilter(MainGroup.abonement_mode), F.text == cmd["new_abonement"])
async def process_add_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info("FSM: abonement: BEGIN new abonement")
    await state.set_state(AbonementGroup.name)
    # Ask Abonement name
    await message.answer(
        **as_list(
            Bold(msg["ab_new_name"]), msg["ab_new_name_format"], msg["cancel"]
        ).as_kwargs(),
        reply_markup=kb.empty_kb,
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
    logger.info("FSM: abonement: GOOD NAME for abonement")
    name = await state.get_value("name")
    if message.text and message.text == "/skip" and name is not None:
        logger.info("FSM: abonement: SKIP name for abonement")
    else:
        # Check Abonement name
        name = message.text.strip() if message.text else None
        if not name or not name.isprintable():
            await message.answer(msg["ab_new_wrong_name"])
            return
    # Save Abonement name
    await state.update_data(name=name)
    await state.set_state(AbonementGroup.total_visits)
    # Ask about total visits
    tokens = [Bold(msg["ab_new_visits"]), Text(msg["ab_zero_visits"])]
    if await state.get_value("abonement_id"):
        total_visits = await state.get_value("total_visits")
        tokens.append(as_key_value(msg["current"], total_visits))
        tokens.append(Text(msg["skip"]))
    await message.answer(**as_list(*tokens).as_kwargs(), reply_markup=kb.empty_kb)


# Add or Edit Abonement: WRONG name
@router.message(StateFilter(AbonementGroup.name))
async def process_wrong_name_abonement_command(message: Message) -> None:
    logger.info("FSM: abonement: WRONG NAME for abonement")
    await message.answer(msg["ab_new_wrong_name"])


# Add or Edit Abonement: GOOD total visits
@router.message(
    StateFilter(AbonementGroup.total_visits),
    or_f(Command("empty", "skip"), F.text.isdigit()),
)
async def process_good_visits_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info("FSM: abonement: GOOD total visits for abonement")
    total_visits = await state.get_value("total_visits")
    if message.text == "/skip" and total_visits is not None:
        logger.info("FSM: abonement: SKIP total visits for abonement")
    else:
        # Check Abonement total visits
        if message.text == "/empty":
            total_visits = 0
        else:
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
    await state.set_state(AbonementGroup.expiry_date)
    # Ask about expiry date
    tokens = [
        Text(msg["ab_new_expiry_date"], " ", msg["date_format"]),
        as_key_value(msg["example"], datetime.now().strftime(date_fmt)),
        Text(msg["ab_new_no_expiry_date"]),
    ]
    if await state.get_value("abonement_id"):
        expiry_date_str = await state.get_value("expiry_date")
        if expiry_date_str:
            expiry_date = datetime.fromisoformat(expiry_date_str)
            tokens.append(as_key_value(msg["current"], expiry_date.strftime(date_fmt)))
        tokens.append(Text(msg["skip"]))
    await message.answer(
        **as_list(*tokens).as_kwargs(),
        reply_markup=kb.empty_kb,
    )


# Add or Edit Abonement: WRONG total visits
@router.message(StateFilter(AbonementGroup.total_visits))
async def process_wrong_visits_abonement_command(message: Message) -> None:
    logger.info("FSM: abonement: WRONG TOTAL visits for abonement")
    await message.answer(msg["ab_wrong_visits"])


# Add or Edit Abonement: GOOD expiry date
@router.message(
    StateFilter(AbonementGroup.expiry_date), or_f(Command("empty", "skip"), F.text)
)
async def process_good_expiry_date_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info("FSM: abonement: GOOD expiry date for abonement")
    expiry_date_str = await state.get_value("expiry_date")
    expiry_date = datetime.fromisoformat(expiry_date_str) if expiry_date_str else None
    if message.text == "/skip":
        logger.info("FSM: abonement: SKIP expiry date for abonement")
    else:
        # Check Abonement expiry date
        user_input = message.text
        expiry_date = None
        if not user_input:
            logger.warning("FSM: abonement: no expiry date")
            await message.answer(msg["ab_wrong_expiry_date"])
            return
        if user_input != "/empty":
            try:
                expiry_date = datetime.strptime(user_input, date_fmt)
            except ValueError:
                logger.warning("FSM: abonement: wrong expiry date")
                await message.answer(msg["ab_wrong_expiry_date"])
                return
    # Save Abonement expiry date
    await state.update_data(
        expiry_date=expiry_date.isoformat() if expiry_date else None
    )
    await state.set_state(AbonementGroup.description)
    # Ask about description
    tokens = [
        Text(msg["ab_new_descr"]),
        Text(msg["ab_new_empty_descr"]),
    ]
    if await state.get_value("abonement_id"):
        description = await state.get_value("description")
        if not description:
            description = msg["none"]
        tokens.append(as_key_value(msg["current"], description))
        tokens.append(Text(msg["skip"]))
    await message.answer(
        **as_list(*tokens).as_kwargs(),
        reply_markup=kb.empty_kb,
    )


# Add or Edit Abonement: WRONG expiry date
@router.message(StateFilter(AbonementGroup.expiry_date))
async def process_wrong_expiry_date_abonement_command(message: Message) -> None:
    logger.info("FSM: abonement: WRONG expiry date for abonement")
    await message.answer(msg["ab_wrong_expiry_date"])


# Add or Edit Abonement: GOOD description
@router.message(
    StateFilter(AbonementGroup.description), or_f(Command("empty", "skip"), F.text)
)
async def process_good_description_abonement_command(
    message: Message, state: FSMContext, user_id: int, db: Database
) -> None:
    logger.info("FSM: abonement: GOOD description for abonement")
    if message.text == "/skip":
        logger.info("FSM: abonement: SKIP description for abonement")
    else:
        # Check Abonement description
        if message.text == "/empty":
            await state.update_data(description=None)
        elif message.text:
            await state.update_data(description=message.text.strip())
    user = await db.user_by_id(user_id)
    abonement_name = await state.get_value("name")
    total_visits = await state.get_value("total_visits")
    description = await state.get_value("description")
    abonement_id = await state.get_value("abonement_id")
    expiry_str = await state.get_value("expiry_date")
    expiry_date = datetime.fromisoformat(expiry_str) if expiry_str else None
    if not user or not abonement_name or total_visits is None:
        logger.warning(f"FSM: abonement: user {user_id} not found or wrong state")
        return
    # Save UPDATED Abonement
    if abonement_id:
        is_update = True
        abonement = await db.abonement_edit(
            abonement_id=abonement_id,
            name=abonement_name,
            owner=user,
            total_visits=total_visits if total_visits else 0,
            expiry_date=expiry_date if expiry_date else None,
            description=description if description else None,
        )
        if abonement:
            logger.info(f"Updated abonement {abonement.id}")
        else:
            logger.warning(
                f"FSM: abonement: can't update {abonement_id} for user {user_id}"
            )
    # Save NEW Abonement
    else:
        is_update = False
        abonement = await db.abonement_create(
            name=abonement_name,
            owner=user,
            total_visits=total_visits,
            expiry_date=expiry_date,
            description=description,
        )
        if abonement:
            logger.info(f"Created new abonement {abonement.id}")
            abonement_id = abonement.id
        else:
            logger.warning("FSM: abonement: can't create new abonement")
    # Create/update spreadsheet for Abonement
    if abonement_id:
        queue_publisher.result(
            {
                "job_type": "abonement_update",
                "abonement_id": abonement_id,
            }
        )
    # Reset state to Abonenment mode
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    if not abonement:
        return
    # Show info about Abonement
    key = abonement.token
    if is_update:
        # EDITED Abonement info
        await message.answer(
            **as_list(
                msg["ab_edit_done"],
                Bold(abonement.name),
                Italic(abonement.description) if abonement.description else "",
                Text(
                    Bold(msg["ab_expiry_date_label"]),
                    " ",
                    (
                        abonement.expiry_date.strftime(date_fmt)
                        if abonement.expiry_date
                        else msg["ab_unlim"]
                    ),
                ),
                as_key_value(
                    msg["ab_total_visits"],
                    (
                        abonement.total_visits
                        if abonement.total_visits
                        else Italic(msg["ab_unlim"])
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
    logger.info("FSM: abonement: WRONG description for abonement")
    await message.answer(
        **as_list(msg["ab_new_wrong_descr"], msg["ab_new_empty_descr"]).as_kwargs()
    )


#
# Abonement join: BEGIN
#
@router.message(StateFilter(MainGroup.abonement_mode), F.text == cmd["join_abonement"])
async def process_join_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info("FSM: abonement: BEGIN join abonement")
    await state.set_state(AbonementGroup.join)
    await message.answer(
        **as_list(msg["ab_join_begin"], Bold(msg["ab_join_key"])).as_kwargs(),
        reply_markup=kb.empty_kb,
    )


# Abonement join: GOOD key
@router.message(StateFilter(AbonementGroup.join), F.text)
async def process_good_key_join_abonement_command(
    message: Message, state: FSMContext, user_id: int, db: Database
) -> None:
    logger.info("FSM: abonement: GOOD key for join abonement")
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
        reply_markup=kb.yes_no_kb,
    )


# Abonement join: WRONG key
@router.message(StateFilter(AbonementGroup.join))
async def process_wrong_key_join_abonement_command(message: Message) -> None:
    logger.info("FSM: abonement: WRONG key for join abonement")
    await message.answer(
        **as_list(msg["ab_wrong_key_format"], Bold(msg["uuid_format"])).as_kwargs()
    )


# Abonement join: GOOD accept answer
@router.message(StateFilter(AbonementGroup.accept), F.text.in_([cmd["yes"], cmd["no"]]))
async def process_good_accept_join_abonement_command(
    message: Message, state: FSMContext, db: Database
) -> None:
    logger.info("FSM: abonement: GOOD accept answer for join abonement")
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
        logger.warning("FSM: abonement: wrong state")
        return
    await db.abonement_user_add(
        user_id=user_id, abonement_id=abonement_id, abonement_token=abonement_token
    )
    await message.answer(msg["ab_join_ok"], reply_markup=kb.get_abonement_kb())


# Abonement join: WRONG accept answer
@router.message(StateFilter(AbonementGroup.accept))
async def process_wrong_accept_join_abonement_command(message: Message) -> None:
    logger.info("FSM: abonement: WRONG accept answer for join abonement")
    await message.answer(msg["ab_wrong_yes_no"])


# Abonement delete: got answer
@router.message(StateFilter(AbonementGroup.delete))
async def process_good_delete_abonement_command(
    message: Message, state: FSMContext, db: Database, user_id: int
) -> None:
    logger.info("FSM: abonement: GOOD delete answer for abonement")
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


# Abonement Visit edit: got answer
@router.message(StateFilter(AbonementGroup.visit_edit_confirm))
async def process_visit_edit_command(
    message: Message, state: FSMContext, db: Database, user_id: int
) -> None:
    logger.info("FSM: abonement: GOOD answer for abonement visit edit")
    # Collect data
    data = await state.get_data()
    visit_id_str = data.get("visit_id")
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    if not message.text or not visit_id_str:
        logger.info("FSM: abonement: no date for visit")
        await message.answer(msg["not_done"], reply_markup=kb.get_abonement_kb())
        return
    user_input = message.text.strip()
    visit_id = int(visit_id_str)
    # Check date format
    try:
        visit_date = datetime.strptime(user_input, date_h_m_fmt)
        logger.info("FSM: abonement: set date %s for visit %s", visit_date, visit_id)
    except ValueError:
        logger.warning("FSM: abonement: wrong expiry date")
        await message.answer(msg["not_done"], reply_markup=kb.get_abonement_kb())
        return
    # Get old Visit
    visit = await db.abonement_visit_get(visit_id)
    visit_date_old = visit.ts.strftime(date_h_m_fmt) if visit else None
    # Set Visit date
    result = await db.abonement_visit_update(visit_id, user_id, visit_date)
    if result:
        queue_publisher.result(
            {
                "job_type": "abonement_visit",
                "msg_type": "visit_edit",
                "abonement_id": visit.abonement_id if visit else None,
                "visit_id": visit_id,
                "visit_user_id": visit.user_id if visit else None,
                "user_id": user_id,
                "ts": visit_date_old,
                "ts_new": visit_date.strftime(date_h_m_fmt),
            }
        )
        await message.answer(msg["done"], reply_markup=kb.get_abonement_kb())
    else:
        await message.answer(msg["not_done"], reply_markup=kb.get_abonement_kb())


# Abonement Visit delete: got answer
@router.message(StateFilter(AbonementGroup.visit_delete_confirm))
async def process_visit_delete_command(
    message: Message, state: FSMContext, db: Database, user_id: int
) -> None:
    logger.info("FSM: abonement: GOOD answer for abonement visit delete")
    # Collect data
    data = await state.get_data()
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    visit_id = data.get("visit_id")
    if message.text and message.text.strip().lower() == cmd["txt_yes"] and visit_id:
        # Get old Visit
        visit = await db.abonement_visit_get(visit_id)
        visit_date = visit.ts.strftime(date_h_m_fmt) if visit else None
        # Delete Visit
        result = await db.abonement_visit_delete(visit_id=visit_id, user_id=user_id)
        logger.info("FSM: abonement: visit %s deleted: %s", visit_id, result)
        if result:
            queue_publisher.result(
                {
                    "job_type": "abonement_visit",
                    "msg_type": "visit_delete",
                    "abonement_id": visit.abonement_id if visit else None,
                    "visit_id": visit_id,
                    "visit_user_id": visit.user_id if visit else None,
                    "user_id": user_id,
                    "ts": visit_date,
                }
            )
            await message.answer(msg["done"], reply_markup=kb.get_abonement_kb())
            return
    # Don't delete Visit
    logger.info("FSM: abonement: visit %s not deleted", visit_id)
    await message.answer(msg["not_done"], reply_markup=kb.get_abonement_kb())


# Unknown command for Abonement mode and Abonement Control mode
@router.message(
    or_f(StateFilter(MainGroup.abonement_mode), StateFilter(AbonementGroup))
)
async def process_abonement_unknown_command(message: Message) -> None:
    logger.info("FSM: abonement: unknown command")
    await message.answer(msg["ab_unknown"])
