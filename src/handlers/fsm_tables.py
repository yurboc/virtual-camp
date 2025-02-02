import logging
import uuid
import keyboards.reply as kb
from typing import Optional
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, as_list, as_key_value
from const.states import MainGroup
from storage.db_api import Database
from modules import queue_publisher
from utils.config import tables
from const.text import cmd, msg, help

logger = logging.getLogger(__name__)
router = Router(name=__name__)

# Get possible jobs
possible_jobs = []
for table in tables:
    possible_jobs.append(table["title"])
possible_jobs.append(cmd["all"])


# Get job by name
def get_job_by_name(title: Optional[str]) -> Optional[str]:
    if title is None:
        return None
    for table in tables:
        if table["title"] == title:
            return table["generator_name"]
    if title == cmd["all"]:
        return "all"
    return None


# Entering FST-OTM Tables Generator mode
@router.message(
    StateFilter(default_state),
    or_f(Command("tables"), F.text == cmd["tables"]),
)
async def process_generator_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("FSM: generator: entering generator mode")
    if "fst_otm" not in user_type:
        logger.warning("FSM: generator: no access")
        await state.clear()
        await message.answer(msg["no_access"], reply_markup=kb.get_main_kb(user_type))
        return
    await state.set_state(MainGroup.generator_mode)
    await message.answer(msg["table_main"], reply_markup=kb.get_generator_kb())


# Selected table for Generator
@router.message(StateFilter(MainGroup.generator_mode), F.text.in_(possible_jobs))
async def process_selected_table(
    message: Message, state: FSMContext, db: Database, user_id: int
) -> None:
    logger.info(f"FSM: generator: selected table {message.text}")
    job = get_job_by_name(message.text)
    if job is None:
        logger.warning(f"FSM: generator: job {message.text} not found")
        await message.answer(msg["table_bad_task"])
        return
    task_uuid = str(uuid.uuid4())
    user = await db.user_by_id(user_id)
    if not user:
        logger.warning(f"FSM: generator: user {user_id} not found in DB")
        return
    task = await db.task_add(task_uuid=task_uuid, user=user)
    queue_msg = {
        "uuid": task_uuid,
        "task_id": task.id,
        "job_type": "table_generator",
        "job": job,
    }
    queue_publisher.task(queue_msg)
    await message.answer(
        **as_list(msg["table_generating"], as_key_value("ID", task.id)).as_kwargs(),
        reply_markup=kb.go_home_kb,
    )


# Help command for Generator
@router.message(StateFilter(MainGroup.generator_mode), Command("help"))
async def process_help_command(message: Message) -> None:
    logger.info("FSM: generator: help command")
    content_list = [Text(help["table_cmd"])]
    for table in tables:
        content_list.append(
            as_key_value(key=table["generator_name"], value=table["title"])
        )
    content_list.append(as_key_value(key="all", value=cmd["all"]))
    content = Text(as_list(*content_list))
    await message.answer(**content.as_kwargs())


# Cancel command for Generator
@router.message(
    StateFilter(MainGroup.generator_mode),
    (or_f(Command("cancel"), F.text == cmd["exit"])),
)
async def process_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("FSM: generator: cancel command")
    await state.clear()
    await message.answer(text=msg["table_end"], reply_markup=kb.get_main_kb(user_type))


# Unknown command for Generator
@router.message(StateFilter(MainGroup.generator_mode))
async def process_unknown_command(message: Message) -> None:
    logger.info("FSM: generator: unknown command")
    await message.answer(msg["table_unknown"])
