import logging
import subprocess
import keyboards.reply as kb
import requests
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import Text, Bold, Pre, Code
from aiogram.utils.formatting import as_list, as_key_value
from aiogram.utils.formatting import as_numbered_section, as_marked_section
from requests.auth import HTTPBasicAuth
from const.states import MainGroup
from storage.db_api import Database
from const.text import cmd, msg, help
from const.groups import groups

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Get Bot version
def get_bot_version() -> str:
    try:
        version = (
            subprocess.check_output(["git", "describe", "--long", "--tags", "--always"])
            .decode("utf-8")
            .strip()
        )
    except Exception:
        version = "unknown"
    logger.info(f"Bot version: {version}")
    return version


# Get RabbitMQ queues
def get_rabbitmq_queues_status(
    host="localhost", port="15672", username="guest", password="guest"
) -> list[str]:
    url = f"http://{host}:{port}/api/queues"
    result = []
    try:
        response = requests.get(url, auth=HTTPBasicAuth(username, password))
        response.raise_for_status()  # exception for status code 4xx and 5xx
        queues = response.json()
        for queue in queues:
            result.append(
                f"{queue['name']:<15}: {queue.get('state', 'unknown')},"
                f" messages={queue['messages']}, consumers={queue['consumers']}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to RabbitMQ: {e}")
    return result


# Entering diagnostic mode
@router.message(
    StateFilter(default_state), or_f(Command("diag"), F.text == cmd["diag"])
)
async def process_diag_command(message: Message, state: FSMContext) -> None:
    logger.info("FSM: diag: entering diag mode")
    await state.set_state(MainGroup.diag_mode)
    await message.answer(text=msg["diag_main"], reply_markup=kb.empty_kb)


# Command /help in diag state
@router.message(StateFilter(MainGroup.diag_mode), Command("help"))
async def process_help_command(message: Message):
    logger.info("FSM: diag: help command")
    await message.answer(
        **Text(as_list(Bold(help["diag_cmd"]), help["diag_info"])).as_kwargs()
    )


# Command /cancel in diag state
@router.message(StateFilter(MainGroup.diag_mode), Command("cancel"))
async def process_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
):
    logger.info(f"FSM: diag: cancel command, user_type={user_type}")
    await state.clear()
    await message.answer(
        text=msg["diag_cancel"],
        reply_markup=kb.get_main_kb(user_type),
    )


# Command /info in diag state
@router.message(Command("info"))
async def process_info_command(
    message: Message,
    state: FSMContext,
    db: Database,
    user_id: int,
    user_tg_id: int,
    user_type: list[str],
) -> None:
    logger.info(f"FSM: diag: info command, user_id={user_id}, user_type={user_type}")
    # Get user info
    user = await db.user_by_id(user_id)
    access_list: list[Text] = []
    for k, v in groups.items():
        if k in user_type:
            access_list.append(Text(msg["m_yes"], v))
        else:
            access_list.append(Text(msg["m_no"], v))
    # Get bot info
    version = get_bot_version()
    state_name = await state.get_state()
    # Create message
    content = as_list(
        as_marked_section(
            Bold(msg["diag_sys_info"]),
            as_key_value(msg["diag_version"], Code(version)),
            as_key_value(msg["diag_state"], Code(state_name)),
        ),
        "",
        as_marked_section(
            Bold(msg["diag_bot_info"]),
            as_key_value("user_id", user_id),
            as_key_value("user_tg_id", user_tg_id),
            as_key_value("user_type", user_type),
        ),
        "",
        as_numbered_section(
            Bold(msg["access_list"]),
            *access_list,
        ),
        "",
        Bold(msg["diag_db_info"]),
        Pre(user),
        "",
        Bold(msg["diag_rabbitmq_info"]),
        Code(as_list(*get_rabbitmq_queues_status())),
    )
    # Send message
    await message.answer(
        **content.as_kwargs(),
        reply_markup=kb.empty_kb,
    )


# All other messages in diag state
@router.message(StateFilter(MainGroup.diag_mode))
async def process_any_message(message: Message) -> None:
    logger.info("FSM: diag: any message")
    content = Text(
        msg["diag_any_msg"],
        Pre(message.model_dump_json(indent=4, exclude_none=True), language="JSON"),
    )
    await message.answer(
        **content.as_kwargs(),
        reply_markup=kb.empty_kb,
    )
