import logging
from typing import Optional
from aiogram import Router
from aiogram.utils.formatting import Text, Bold, as_list
from storage.db_api import Database
from storage.db_schema import TgAbonement, TgInvite
from const.text import msg

logger = logging.getLogger(__name__)
router = Router(name=__name__)


async def handle_abonement(
    token: str, db: Database, user_id: int
) -> tuple[Optional[TgAbonement], Text]:
    # Try to find Abonement by token
    abonement = await db.abonement_by_token(token)
    if not abonement:
        return None, Text(msg["ab_wrong_key"])
    # Abonement found. Check if abonement is active
    if abonement.hidden:
        return None, as_list(msg["ab_join_deleted"], Bold(abonement.name))
    # Check user is not owner
    if abonement.owner_id == user_id:
        return abonement, Text(msg["ab_wrong_owner"])
    # Check user is not already in Abonement
    if await db.abonement_user(user_id=user_id, abonement_id=abonement.id):
        return abonement, Text(msg["ab_join_already"])
    # Add user to Abonement
    res = await db.abonement_user_add(
        user_id=user_id, abonement_id=abonement.id, abonement_token=abonement.token
    )
    # Set Abonement state
    if res:
        return abonement, Text(as_list(msg["ab_joined"], Bold(abonement.name)))
    else:
        return None, Text(msg["ab_err_unknown"])


async def handle_invite(
    token: str, db: Database, user_id: int, user_type: list[str]
) -> tuple[Optional[TgInvite], Text]:
    # Get group type by povided token
    invite = await db.invite_by_token(token)
    if not invite:
        return None, Text(msg["invite_err_key"])
    # Check user is not already in priveleged group
    if invite.group in user_type:
        return invite, Text(msg["invite_err_joined"])
    # Add user to priveleged group
    res = await db.invite_accept(user_id=user_id, invite=invite)
    if res:
        return invite, as_list(msg["invite_ok"], msg["start"])
    else:
        return None, Text(msg["invite_err_unknown"])
