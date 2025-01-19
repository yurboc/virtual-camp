import logging
import json
import pika
import uuid
import keyboards.common as kb
from typing import Optional
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Bold, as_list, as_key_value
from const.states import PicturesGroup
from const.text import cmd, msg, help
from storage.db_api import Database
from utils.config import config, pictures

logger = logging.getLogger(__name__)
router = Router(name=__name__)

#
# UTILS
#

# Get possible jobs
possible_jobs = []
for picture in pictures:
    possible_jobs.append(picture["title"])


# Get job by name
def get_job_by_name(title: Optional[str]) -> Optional[dict]:
    if title is None:
        return None
    for picture in pictures:
        if picture["title"] == title:
            return picture
    return None


# Publish RabbitMQ message
def queue_publish_message(msg: dict) -> None:
    logger.info("Publishing message...")
    message_json = json.dumps(msg)
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    queue = config["RABBITMQ"]["QUEUES"]["TASKS"]
    channel.queue_declare(queue=queue)
    logger.info("Publish to %s: %s", queue, message_json)
    channel.basic_publish(exchange="", routing_key=queue, body=message_json)
    connection.close()
    logger.info("Done publishing message!")


#
# HANDLERS
#


# Cancel command for Pictures mode
@router.message(
    StateFilter(PicturesGroup), or_f(Command("cancel"), F.text == cmd["exit"])
)
async def process_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("FSM: pictures: cancel command")
    await state.clear()
    await message.answer(
        text=msg["pictures_end"], reply_markup=kb.get_main_kb(user_type)
    )


# Help command for Pictures mode
@router.message(StateFilter(PicturesGroup), Command("help"))
async def process_help_command(message: Message) -> None:
    logger.info("FSM: pictures: help command")
    await message.answer(
        **as_list(Bold(help["pictures_cmd"]), help["pictures_cancel"]).as_kwargs()
    )


# Entering Pictures mode
@router.message(
    StateFilter(default_state), or_f(Command("pictures"), F.text == cmd["pictures"])
)
async def process_entering_mode_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info("FSM: pictures: entering pictures mode")
    if "youtube_adm" not in user_type:
        logger.warning("FSM: pictures: no access")
        await state.clear()
        await message.answer(msg["no_access"], reply_markup=kb.get_main_kb(user_type))
        return
    await state.set_state(PicturesGroup.background)
    await message.answer(
        msg["pictures_main"], reply_markup=kb.get_pictures_kb(select_mode=True)
    )


# Selected Picture output type
@router.message(
    StateFilter(PicturesGroup.background),
    F.text.in_([cmd["as_picture"], cmd["as_document"]]),
)
async def process_output_type(message: Message, state: FSMContext) -> None:
    logger.info("FSM: pictures: set output type")
    if message.text and message.text == cmd["as_picture"]:
        await state.update_data({"output_type": "picture"})
        logger.info("FSM: pictures: output as picture")
    elif message.text and message.text == cmd["as_document"]:
        await state.update_data({"output_type": "document"})
        logger.info("FSM: pictures: output as document")
    else:
        logger.warning(f"FSM: pictures: unknown output type: {message.text}")
        return
    await message.answer(
        msg["pictures_output_mode"], reply_markup=kb.get_pictures_kb(select_mode=False)
    )


#  Selected Picture
@router.message(StateFilter(PicturesGroup.background), F.text.in_(possible_jobs))
async def process_selected_picture(message: Message, state: FSMContext) -> None:
    logger.info("FSM: pictures: selected picture")
    picture = get_job_by_name(message.text)
    if picture is None:
        logger.warning(f"FSM: pictures: job {message.text} not found")
        await message.answer(msg["pictures_bad_task"])
        return
    await state.update_data({"picture": picture})
    await state.set_state(PicturesGroup.text)
    await message.answer(msg["pictures_text"], reply_markup=kb.empty_kb)


# Add text for Picture
@router.message(StateFilter(PicturesGroup.text), F.text)
async def process_text(
    message: Message, state: FSMContext, db: Database, user_id: int
) -> None:
    logger.info("FSM: pictures: got text")
    # Check text
    text = message.text.strip() if message.text else ""
    lines_list_orig = text.split("\n")
    lines_list_cleaned = []
    for line in lines_list_orig:
        line = line.strip()
        if line:
            lines_list_cleaned.append(line)
    if len(lines_list_cleaned) not in [1, 2]:
        await message.answer(msg["pictures_bad_text"])
        return
    # Create task
    picture = await state.get_value("picture")
    output_type = await state.get_value("output_type")
    task_uuid = str(uuid.uuid4())
    user = await db.user_by_id(user_id)
    if not user:
        logger.warning(f"FSM: pictures: user {user_id} not found in DB")
        return
    task = await db.task_add(task_uuid=task_uuid, user=user)
    if not task:
        logger.warning(f"FSM: pictures: task {task_uuid} not created in DB")
        return
    queue_msg = {
        "uuid": task_uuid,
        "task_id": task.id,
        "job_type": "pictures_generator",
        "picture": picture,
        "lines": lines_list_cleaned,
        "output_type": output_type,
    }
    logger.debug(f"FSM: pictures: task '{queue_msg}' prepared")
    queue_publish_message(queue_msg)
    await message.answer(
        **as_list(msg["pictures_generating"], as_key_value("ID", task.id)).as_kwargs(),
        reply_markup=kb.go_home_kb,
    )


# Unknown command for Pictures mode
@router.message(StateFilter(PicturesGroup))
async def process_unknown_command(message: Message) -> None:
    logger.info("FSM: pictures: unknown command")
    await message.answer(msg["pictures_unknown"])
