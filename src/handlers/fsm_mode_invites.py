import logging
import keyboards.common as kb
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Bold, as_list
from const.states import InvitesGroup
from const.text import cmd, msg, help

logger = logging.getLogger(__name__)
router = Router(name=__name__)


#
# HANDLERS
#


# Cancel command for Invites mode
@router.message(
    StateFilter(InvitesGroup),
    (or_f(Command("cancel"), F.text.in_([cmd["exit"], cmd["go_home"]]))),
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


#
#
# Handlers will be here
#
#


# Unknown command for Invites mode
@router.message(StateFilter(InvitesGroup))
async def process_unknown_command(message: Message) -> None:
    logger.info("FSM: invites: unknown command")
    await message.answer(msg["invites_unknown"])
