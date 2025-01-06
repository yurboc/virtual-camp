import logging
import keyboards.common as kb
import re
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Text, Bold, Italic, as_list
from storage.db_api import Database

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
    logger.info(f"Got START command with deep linking")
    logger.info(f"Got link parameters: {command.args}")
    args = command.args.split("_") if command.args else []
    # DEEP LINKING: MODE 'abonement': try to join to Abonement of another user
    if (
        len(args) == 2
        and args[0] == "abonement"
        and re.search(
            r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", args[1]
        )
    ):
        # Try to find Abonement by token
        abonement = await db.abonement_by_token(args[1])
        if not abonement:
            await message.answer(text="Неверный ключ абонемента.")
            return
        # Check user is not owner
        if abonement.owner_id == user_id:
            await message.answer(text="Нельзя присоединиться к своему абонементу.")
            return
        # Check user is not already in Abonement
        if await db.abonement_user(user_id=user_id, abonement_id=abonement.id):
            await message.answer(text="Вы уже присоединены к этому абонементу.")
            return
        # Add user to Abonement
        await db.abonement_user_add(
            user_id=user_id, abonement_id=abonement.id, abonement_token=abonement.token
        )
        # Set Abonement state
        await message.answer(
            **Text(
                as_list("Вы успешно присоединились к абонементу", Bold(abonement.name))
            ).as_kwargs()
        )
    else:
        # Default start with wrong parameters
        await state.clear()
        await message.answer(
            **Text(
                as_list(
                    "Вас приветствует бот Virtual Camp!",
                    "",
                    Italic("Параметры распознать не удалось."),
                    "Вы в главном меню.",
                )
            ).as_kwargs(),
            reply_markup=kb.get_main_kb(user_type),
        )
