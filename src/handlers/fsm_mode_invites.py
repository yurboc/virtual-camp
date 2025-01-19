import logging
import uuid
import keyboards.common as kb
from typing import Optional
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.formatting import Bold, Code, as_list, as_key_value
from storage.db_api import Database
from const.states import InvitesGroup
from const.text import cmd, msg, help, user_types, date_h_m_s_fmt

logger = logging.getLogger(__name__)
router = Router(name=__name__)

#
# UTILS
#

# Get possible groups
possible_groups = []
for _, v in user_types.items():
    possible_groups.append(v)


# Get group by name
def get_group_by_name(group_name: Optional[str]) -> Optional[str]:
    if group_name is None:
        return None
    for k, v in user_types.items():
        if v == group_name:
            return k
    return None


#
# HANDLERS
#


# Cancel command for Invites mode
@router.message(
    StateFilter(InvitesGroup), (or_f(Command("cancel"), F.text == cmd["exit"]))
)
async def process_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("FSM: invites: cancel command")
    await state.clear()
    await message.answer(
        text=msg["invites_end"], reply_markup=kb.get_main_kb(user_type)
    )


# Help command for Invites mode
@router.message(StateFilter(InvitesGroup), Command("help"))
async def process_help_command(message: Message) -> None:
    logger.info("FSM: invites: help command")
    await message.answer(
        **as_list(Bold(help["invites_cmd"]), help["invites_cancel"]).as_kwargs()
    )


# Entering Invites mode
@router.message(
    StateFilter(default_state), or_f(Command("invites"), F.text == cmd["invites"])
)
async def process_entering_mode_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("FSM: invites: entering invites mode")
    if "invite_adm" not in user_type:
        logger.warning("FSM: invites: no access")
        await state.clear()
        await message.answer(msg["no_access"], reply_markup=kb.get_main_kb(user_type))
        return
    await state.set_state(InvitesGroup.begin)
    await message.answer(msg["invites_main"], reply_markup=kb.invites_kb())


# Ask to create new invite
@router.message(StateFilter(InvitesGroup.begin), F.text == cmd["new_invite"])
async def process_create_invite_command(message: Message, state: FSMContext) -> None:
    logger.info("FSM: invites: create invite command")
    await state.set_state(InvitesGroup.create)
    await message.answer(msg["invites_create"], reply_markup=kb.get_new_invite_kb())


# Create new invite
@router.message(StateFilter(InvitesGroup.create), F.text.in_(possible_groups))
async def process_new_invite_command(
    message: Message, state: FSMContext, db: Database
) -> None:
    logger.info("FSM: invites: create invite command")
    await state.set_state(InvitesGroup.done)
    if not message.text or not message.bot:
        return
    group_name = message.text.strip()
    group = get_group_by_name(group_name=group_name)
    if not group:
        logger.warning("FSM: invites: group %s not found", group_name)
        await message.answer(msg["invites_bad_group"])
        return
    token = str(uuid.uuid4())
    invite = await db.invite_create(token=token, group=group)
    link = await create_start_link(bot=message.bot, payload=f"invite_{token}")
    if not invite:
        logger.warning("FSM: invites: invite not created in DB, token=%s", token)
        return
    res = as_list(
        msg["invites_new"], as_key_value(group, group_name), "", Code(token), "", link
    )
    await message.answer(**res.as_kwargs(), reply_markup=kb.go_home_kb)


# History of invites
@router.message(StateFilter(InvitesGroup.begin), F.text == cmd["invite_history"])
async def process_history_command(
    message: Message, state: FSMContext, db: Database
) -> None:
    logger.info("FSM: invites: history command")
    await state.set_state(InvitesGroup.done)
    invites = await db.invite_list()
    res_items = []
    for invite in invites:
        users = await db.invite_users(invite=invite)
        res_items.append(
            as_list(
                "",
                as_key_value(invite.group, user_types[invite.group]),
                invite.ts_created.strftime(date_h_m_s_fmt),
                Code(invite.token),
                as_key_value(msg["invites_users"], len(users)),
            )
        )
    if not invites:
        res_items.append(as_list("", msg["invites_empty"]))
    res_message = as_list(msg["invites_history"], *res_items)
    await message.answer(**res_message.as_kwargs(), reply_markup=kb.go_home_kb)


# Unknown command for Invites mode
@router.message(StateFilter(InvitesGroup))
async def process_unknown_command(message: Message) -> None:
    logger.info("FSM: invites: unknown command")
    await message.answer(msg["invites_unknown"])
