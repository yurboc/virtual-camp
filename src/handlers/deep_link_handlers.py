import logging
import keyboards.common as kb
import re
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Text, Bold, Italic, as_list
from storage.db_api import Database
from const.text import msg, re_uuid

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Command /start with deep linking
@router.message(CommandStart(deep_link=True))
async def command_start_handler(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    db: Database,
    user_id: int,
    user_type: list[str],
) -> None:
    logger.info("Got START command with deep linking")
    logger.info(f"Got link parameters: {command.args}")
    args = command.args.split("_") if command.args else []
    # DEEP LINKING: MODE 'abonement': try to join to Abonement of another user
    if len(args) == 2 and args[0] == "abonement" and re.search(re_uuid, args[1]):
        # Try to find Abonement by token
        abonement = await db.abonement_by_token(args[1])
        if not abonement:
            await message.answer(text=msg["ab_wrong_key"])
            return
        # Check user is not owner
        if abonement.owner_id == user_id:
            await message.answer(text=msg["ab_wrong_owner"])
            return
        # Check user is not already in Abonement
        if await db.abonement_user(user_id=user_id, abonement_id=abonement.id):
            await message.answer(text=msg["ab_already_joined"])
            return
        # Add user to Abonement
        await db.abonement_user_add(
            user_id=user_id, abonement_id=abonement.id, abonement_token=abonement.token
        )
        # Set Abonement state
        await message.answer(
            **Text(as_list(msg["ab_joined"], Bold(abonement.name))).as_kwargs()
        )
    # DEEP LINKING: MODE 'invite': add user to priveleged group
    elif len(args) == 2 and args[0] == "invite" and re.search(re_uuid, args[1]):
        # Get group type by povided token
        invite = await db.invite_by_token(args[1])
        if not invite:
            await message.answer(text=msg["invite_err_key"])
            return
        # Check user is not already in priveleged group
        if invite.group in user_type:
            await message.answer(text=msg["invite_err_joined"])
            return
        # Add user to priveleged group
        res = await db.invite_accept(user_id=user_id, invite=invite)
        if res:
            await message.answer(text=msg["invite_ok"])
        else:
            await message.answer(text=msg["invite_err_unknown"])
    else:
        # Default start with wrong parameters
        await state.clear()
        await message.answer(
            **Text(
                as_list(
                    msg["hello_bot"], "", Italic(msg["err_params"]), msg["main_menu"]
                )
            ).as_kwargs(),
            reply_markup=kb.get_main_kb(user_type),
        )
