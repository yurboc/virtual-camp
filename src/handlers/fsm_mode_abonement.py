import logging
import keyboards.common as kb
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
from handlers.fsm_define import MainGroup, AbonementGroup
from storage.db_api import Database

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Entering Abonement mode
@router.message(
    StateFilter(default_state),
    or_f(Command(commands=["abonement"]), F.text == "Абонементы"),
)
async def process_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: entering abonement mode")
    await state.set_state(MainGroup.abonement_mode)
    await message.answer(
        **Text(
            as_list(
                "Работа с абонементами",
                "Выберите действие",
            )
        ).as_kwargs(),
        reply_markup=kb.get_abonement_kb(),
    )


# Help command for Abonement
@router.message(StateFilter(MainGroup.abonement_mode), Command(commands=["help"]))
async def process_abonement_help_command(message: Message) -> None:
    logger.info(f"FSM: abonement: help command")
    await message.answer(
        **Text(
            as_list(
                "Режим работы с абонементами:",
                "/cancel - завершить работу с абонементами",
            )
        ).as_kwargs(),
    )


# Cancel command for Abonement
@router.message(
    StateFilter(MainGroup.abonement_mode),
    (or_f(Command(commands=["cancel"]), F.text == "Выход")),
)
async def process_abonement_cancel_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: cancel command")
    await state.clear()
    await message.answer(
        text="Завершение работы с абонементами. Вы в главном меню.",
        reply_markup=kb.get_main_kb(),
    )


# Cancel command for Abonement OPERATION mode
@router.message(
    StateFilter(AbonementGroup),
    (or_f(Command(commands=["cancel"]), F.text == "Выход")),
)
async def process_abonement_op_cancel_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: cancel operation command")
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    await message.answer(
        **Text(
            as_list(
                "Возврат в работу с абонементами",
                "Выберите действие",
            )
        ).as_kwargs(),
        reply_markup=kb.get_abonement_kb(),
    )


# List of Abonement
@router.message(StateFilter(MainGroup.abonement_mode), F.text == "Мои абонементы")
async def process_my_abonements_command(
    message: Message, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: list my abonements")
    user = await db.user_by_tg_id(user_id)
    # Find my abonements
    my_abonements = await db.abonements_list_by_owner(user)
    my_abonements_list = [abonement.name for abonement in my_abonements]
    my_abonements_text = None
    if my_abonements_list:
        my_abonements_text = Text(
            as_list("Мои абонементы:", as_marked_list(*my_abonements_list))
        )
    # Find other abonements
    other_abonements = await db.abonements_list_by_user(user)
    other_abonements_list = [abonement.name for abonement in other_abonements]
    other_abonements_text = None
    if other_abonements_list:
        other_abonements_text = Text(
            as_list("Абонементы друзей:", as_marked_list(*other_abonements_list))
        )
    # Combine abonements info
    if my_abonements_text or other_abonements_text:
        content = Text(
            as_list(
                *my_abonements_text if my_abonements_text else [],
                *other_abonements_text if other_abonements_text else [],
                "С каким абонементом работаем?",
            )
        )
    else:
        content = Text(
            "Абонементы отсутствуют. Создайте новый или присоединитесь к существующему."
        )
    await message.answer(**content.as_kwargs())


#
# Add new Abonement: BEGIN
#
@router.message(StateFilter(MainGroup.abonement_mode), F.text == "Создать абонемент")
async def process_add_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: BEGIN new abonement")
    await state.set_state(AbonementGroup.abonement_name)
    await message.answer(
        **as_list(
            "Начинаем создание нового абонемента.",
            "",
            Bold("Введите название абонемента"),
            "Формат: <Куда> до <дата> на <Владелец>",
            "",
            "Всю остальную информацию введём на следующих шагах.",
            "/cancel - отменить создание абонемента",
        ).as_kwargs(),
        reply_markup=kb.no_keyboard,
    )


# Add new Abonement: GOOD ABONEMENT NAME
@router.message(
    StateFilter(AbonementGroup.abonement_name),
    F.text,
    or_f(F.text.isprintable(), F.text.isspace()),
)
async def process_good_name_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: GOOD NAME for abonement")
    # Check Abonement name
    name = message.text.strip() if message.text else None
    if not name or not name.isprintable():
        await message.answer(
            **as_list(
                "Имя абонемента неверное.",
                "Попробуйте другое.",
                "Выход - /cancel",
            ).as_kwargs()
        )
        return
    # Save Abonement name
    await state.update_data(name=name)
    await state.set_state(AbonementGroup.abonement_total_passes)
    await message.answer(
        **as_list(
            "Хорошо, имя запомнили.",
            "",
            Bold("Введите количество посещений"),
            "Пример: 60",
            "Введите 0, если не нужно проверять количество посещений",
            "",
            "Всю остальную информацию введём на следующих шагах.",
            "/cancel - отменить создание абонемента",
        ).as_kwargs(),
    )


# Add new Abonement: WRONG ABONEMENT NAME
@router.message(StateFilter(AbonementGroup.abonement_name))
async def process_wrong_name_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: WRONG NAME for abonement")
    await message.answer(
        **as_list(
            "Имя не подходит. Нужен просто текст.",
            "",
            "Попробуйте другое имя, без спецсимволов.",
            "/cancel - отменить создание абонемента",
        ).as_kwargs()
    )


# Add new Abonement: GOOD ABONEMENT TOTAL PASSES
@router.message(StateFilter(AbonementGroup.abonement_total_passes), F.text.isdigit())
async def process_good_passes_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: GOOD TOTAL PASSES for abonement")
    # Check Abonement total passes
    total_passes = int(message.text) if message.text else 0
    if total_passes > 1000 or total_passes < 0:
        await message.answer(
            **as_list(
                "Неверное количество посещений, максимум 1000.",
                "Если посещения не отслеживаются, введите 0.",
                "Выход - /cancel",
            ).as_kwargs()
        )
        return
    # Save Abonement total passes
    await state.update_data(total_passes=total_passes)
    await state.set_state(AbonementGroup.abonement_description)
    await message.answer(
        **as_list(
            "Хорошо, посещения записали.",
            "",
            Bold("Введите описание абонемента"),
            "Всё, что нужо знать тем, кто пользуется абонементом.",
            "",
            "/skip - не заполнять описание абонемента",
            "/cancel - отменить создание абонемента",
        ).as_kwargs()
    )


# Add new Abonement: WRONG ABONEMENT TOTAL PASSES
@router.message(StateFilter(AbonementGroup.abonement_total_passes))
async def process_wrong_passes_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: WRONG TOTAL PASSES for abonement")
    await message.answer(
        **as_list(
            "Количество посещений не подходит.",
            "",
            "Попробуйте отправить положительное число или 0.",
            "/cancel - отменить создание абонемента",
        ).as_kwargs()
    )


# Add new Abonement: GOOD ABONEMENT DESCRIPTION
@router.message(
    StateFilter(AbonementGroup.abonement_description),
    or_f(Command(commands=["skip"]), F.text),
)
async def process_good_description_abonement_command(
    message: Message, state: FSMContext, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: GOOD description for abonement")
    # Save Abonement
    if message.text == "/skip":
        await state.update_data(description=None)
    else:
        await state.update_data(description=message.text)
    user = await db.user_by_tg_id(user_id)
    abonement = await db.abonement_create(
        name=(await state.get_data()).get("name"),
        owner=user,
        total_passes=(await state.get_data()).get("total_passes"),
        description=(await state.get_data()).get("description"),
    )
    logger.info(f"Created new abonement {abonement.id}")
    # Reset state to Abonenment mode
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    await message.answer(
        **as_list(
            "Абонемент создан.",
            Bold(abonement.name),
            as_key_value("Ключ", Code(abonement.token)),
            "",
            "Вы в меню работы с абонементами.",
            "/cancel - выйти в главное меню",
        ).as_kwargs(),
        reply_markup=kb.get_abonement_kb(),
    )


# Add new Abonement: WRONG ABONEMENT DESCRIPTION
@router.message(StateFilter(AbonementGroup.abonement_description))
async def process_wrong_description_abonement_command(
    message: Message, state: FSMContext
) -> None:
    logger.info(f"FSM: abonement: WRONG description for abonement")
    await message.answer(
        **as_list(
            "Описание абонемента не подходит.",
            "",
            "/skip - не заполнять описание абонемента",
            "/cancel - отменить создание абонемента",
        ).as_kwargs()
    )


# Unknown command for Abonement
@router.message(StateFilter(MainGroup.abonement_mode))
async def process_abonement_unknown_command(message: Message) -> None:
    await message.answer(
        "Неизвестная команда работы с абонементами.\nСправка - /help\nВыход - /cancel"
    )
