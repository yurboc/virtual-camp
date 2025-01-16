import logging
from aiogram import Router
from aiogram.utils.formatting import Text, Bold, as_list
from storage.db_api import Database
from const.text import msg

logger = logging.getLogger(__name__)
router = Router(name=__name__)


async def handle_abonement(token: str, db: Database, user_id: int) -> tuple[bool, Text]:
    # Try to find Abonement by token
    abonement = await db.abonement_by_token(token)
    if not abonement:
        return False, Text(msg["ab_wrong_key"])
    # Check user is not owner
    if abonement.owner_id == user_id:
        return False, Text(msg["ab_wrong_owner"])
    # Check user is not already in Abonement
    if await db.abonement_user(user_id=user_id, abonement_id=abonement.id):
        return False, Text(msg["ab_already_joined"])
    # Add user to Abonement
    res = await db.abonement_user_add(
        user_id=user_id, abonement_id=abonement.id, abonement_token=abonement.token
    )
    # Set Abonement state
    if res:
        return True, Text(as_list(msg["ab_joined"], Bold(abonement.name)))
    else:
        return False, Text(msg["ab_err_unknown"])


async def handle_invite(token: str, db: Database, user_id: int, user_type: list[str]):
    # Get group type by povided token
    invite = await db.invite_by_token(token)
    if not invite:
        return False, Text(msg["invite_err_key"])
    # Check user is not already in priveleged group
    if invite.group in user_type:
        return False, Text(msg["invite_err_joined"])
    # Add user to priveleged group
    res = await db.invite_accept(user_id=user_id, invite=invite)
    if res:
        return True, Text(msg["invite_ok"])
    else:
        return False, Text(msg["invite_err_unknown"])
