import logging
import keyboards.common as kb
import re
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import (
    Text,
    Code,
    Bold,
    Italic,
    TextLink,
    as_list,
    as_key_value,
    as_marked_list,
)
from aiogram.utils.deep_linking import create_start_link
from handlers.fsm_define import MainGroup, AbonementGroup
from keyboards.common import AbonementCallbackFactory
from storage.db_api import Database

logger = logging.getLogger(__name__)
router = Router(name=__name__)


#
# HANDLE CALLBACKS
#


# Open Abonement
@router.callback_query(
    or_f(
        StateFilter(MainGroup.abonement_mode),
        StateFilter(AbonementGroup.abonement_open),
    ),
    AbonementCallbackFactory.filter(F.action == "open"),
)
async def callbacks_abonement_open(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    await callback.answer()
    await state.set_data({"offset": 0, "limit": 10})
    await state.set_state(AbonementGroup.abonement_open)
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or abonement.token != callback_data.token or not user:
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(
                f"Неверный ключ или пользователь. Введите /cancel для выхода.",
            )
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        pass_count = await db.abonement_pass_count(abonement.id)
        my_pass_count = await db.abonement_pass_count(abonement.id, user_id=user.id)
        await callback.message.answer(
            **as_list(
                "Выбран абонемент",
                Bold(abonement.name),
                *(
                    [Italic(abonement.description), ""]
                    if abonement.description
                    else [""]
                ),
                (
                    f"На {abonement.total_passes} посещений"
                    if abonement.total_passes != 0
                    else "Без ограничения посещений"
                ),
                as_key_value("Совершено проходов", pass_count),
                as_key_value("Из них мои проходы", my_pass_count),
                *(
                    [
                        as_key_value(
                            "Осталось проходов",
                            abonement.total_passes - pass_count,
                        ),
                        "",
                    ]
                    if abonement.total_passes != 0
                    else [""]
                ),
                "Выберите действие",
            ).as_kwargs(),
            reply_markup=kb.get_abonement_control_kb(abonement, user.id),
        )


# Accept Abonement pass
@router.callback_query(
    StateFilter(AbonementGroup.abonement_open),
    AbonementCallbackFactory.filter(F.action == "pass"),
)
async def callbacks_abonement_accept_pass(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or abonement.token != callback_data.token or not user:
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(
                "Неверный ключ абонемента или пользователь. Введите /cancel для выхода.",
            )
        return
    abonement_pass = await db.abonement_pass_add(abonement.id, user.id)
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_state(MainGroup.abonement_mode)
        if abonement_pass:
            result = [
                "✅ Проход записан",
                Bold(abonement_pass.ts.strftime("%d.%m.%Y %H:%M:%S")),
            ]
        else:
            result = [
                "❌ Проход не записан",
                Bold("На абонементе не осталось проходов"),
            ]
        await callback.message.answer(
            **as_list(
                *result,
                "Выход в меню управления абонементами",
            ).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
        )


# Reject Abonement
@router.callback_query(
    StateFilter(AbonementGroup.abonement_open),
    AbonementCallbackFactory.filter(F.action == "exit"),
)
async def callbacks_abonement_reject_pass(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    if not abonement or abonement.token != callback_data.token:
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(
                f"Неверный ключ абонемента. Введите /cancel для выхода.",
            )
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_state(MainGroup.abonement_mode)
        await callback.message.answer(
            **as_list(
                "❌ Проход не записан", "Выход в меню управления абонементами"
            ).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
        )


# Share Abonement
@router.callback_query(
    StateFilter(AbonementGroup.abonement_open),
    AbonementCallbackFactory.filter(F.action == "share"),
)
async def callbacks_abonement_share(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    if not abonement or abonement.token != callback_data.token:
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(
                f"Неверный ключ абонемента. Введите /cancel для выхода.",
            )
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_state(MainGroup.abonement_mode)
        await callback.message.answer(
            **as_list(
                "Абонемент:",
                Bold(abonement.name),
                *(
                    [Italic(abonement.description), ""]
                    if abonement.description
                    else [""]
                ),
                "Поделиться:",
                (
                    await create_start_link(
                        bot=callback.message.bot,
                        payload=f"abonement_{abonement.token}",
                    )
                    if callback.message.bot
                    else Bold("недоступно")
                ),
            ).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
        )


# List of visits for Abonement
@router.callback_query(
    StateFilter(AbonementGroup.abonement_open),
    AbonementCallbackFactory.filter(F.action.in_(["history", "prev", "next"])),
)
async def callbacks_abonement_visits(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    if not abonement or abonement.token != callback_data.token:
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(
                f"Неверный ключ абонемента. Введите /cancel для выхода.",
            )
        return
    if callback.message and type(callback.message) == Message:
        # Calculate pagination
        total = await db.abonement_pass_count(abonement.id)
        limit = (await state.get_data()).get("limit", 10)
        offset = (await state.get_data()).get("offset", 0)
        if callback_data.action == "prev":
            if offset == 0:
                return
            offset -= limit
            if offset > limit:
                offset -= limit
            else:
                offset = 0
        elif callback_data.action == "next":
            if offset + limit >= total:
                return
            offset += limit
        await state.set_data({"offset": offset, "limit": limit})
        await callback.message.edit_reply_markup(None)
        # Get visits for current page
        visits_list = await db.abonement_pass_list(
            abonement.id, limit=limit, offset=offset
        )
        visits_text = []
        for visit in visits_list:
            visits_text += [
                Text(
                    visit.ts.strftime("%d.%m.%Y %H:%M"),
                    " ",
                    TextLink(visit.user.name, url=f"tg://user?id={visit.user.tg_id}"),
                    (
                        Text(f" (@{visit.user.tg_username})")
                        if visit.user.tg_username
                        else ""
                    ),
                ),
            ]
        answer = as_list(
            (
                Text(
                    "Проходы с ",
                    Bold(offset + 1),
                    " по ",
                    Bold(offset + len(visits_list)),
                    " из ",
                    Bold(total),
                )
                if total > 0
                else Text("Проходов пока не было.")
            ),
            *(visits_text),
        )
        if callback_data.action in ["prev", "next"]:
            await callback.message.edit_text(
                **answer.as_kwargs(),
                reply_markup=kb.get_abonement_history_kb(
                    abonement, offset, limit, total
                ),
            )
        else:
            await callback.message.answer(
                **answer.as_kwargs(),
                reply_markup=kb.get_abonement_history_kb(
                    abonement, offset, limit, total
                ),
            )


# Edit Abonement
@router.callback_query(
    StateFilter(AbonementGroup.abonement_open),
    AbonementCallbackFactory.filter(F.action == "edit"),
)
async def callbacks_abonement_edit(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if (
        not abonement
        or abonement.token != callback_data.token
        or not user
        or user.id != abonement.owner_id
    ):
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(
                f"Неверный ключ абонемента. Введите /cancel для выхода.",
            )
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_data({"abonement_id": abonement.id})
        await state.set_state(AbonementGroup.abonement_name)
        await callback.message.answer(
            **Text(
                as_list(
                    "Редактирование абонемента",
                    as_key_value("Текущее название", abonement.name),
                    as_key_value(
                        "Текущее описание",
                        (
                            abonement.description
                            if abonement.description
                            else Italic("отсутствует")
                        ),
                    ),
                    as_key_value(
                        "Текущее количество проходов",
                        (
                            abonement.total_passes
                            if abonement.total_passes
                            else Italic("без ограничения посещений")
                        ),
                    ),
                    "",
                    Bold("Введите новое название"),
                    "/cancel - отменить редактирование абонемента",
                )
            ).as_kwargs(),
            reply_markup=kb.no_keyboard,
        )


# Delete Abonement
@router.callback_query(
    StateFilter(AbonementGroup.abonement_open),
    AbonementCallbackFactory.filter(F.action == "delete"),
)
async def callbacks_abonement_delete(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or abonement.token != callback_data.token or not user:
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(
                f"Неверный ключ абонемента. Введите /cancel для выхода.",
            )
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_data(
            {
                "abonement_id": abonement.id,
                "abonement_key": abonement.token,
                "operation": "delete" if user.id == abonement.owner_id else "unlink",
            }
        )
        await state.set_state(AbonementGroup.abonement_delete)
        await callback.message.answer(
            **Text(
                as_list(
                    (
                        "🗑 Удаление абонемента"
                        if user.id == abonement.owner_id
                        else "⚠️ Отключение абонемента"
                    ),
                    as_key_value("Название", abonement.name),
                    "",
                    Text(
                        "Отправьте ",
                        Bold("да"),
                        " в ответ, если хотите ",
                        (
                            Bold("удалить")
                            if user.id == abonement.owner_id
                            else Bold("отключить")
                        ),
                        " его.",
                    ),
                    "",
                    "/cancel - отменить удаление абонемента",
                )
            ).as_kwargs(),
            reply_markup=kb.no_keyboard,
        )


#
# HANDLE MESSAGES
#


# Entering Abonement mode
@router.message(
    StateFilter(default_state),
    or_f(Command("abonement"), F.text == "Абонементы"),
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


# Help command for Abonement mode
@router.message(StateFilter(MainGroup.abonement_mode), Command("help"))
async def process_abonement_mode_help_command(message: Message) -> None:
    logger.info(f"FSM: abonement mode: help command")
    await message.answer(
        **Text(
            as_list(
                "Режим работы с абонементами",
                "/cancel - завершить работу с абонементами",
            )
        ).as_kwargs(),
    )


# Help command for Abonement Control mode
@router.message(StateFilter(AbonementGroup), Command("help"))
async def process_abonement_ctrl_help_command(message: Message) -> None:
    logger.info(f"FSM: abonement control: help command")
    await message.answer(
        **Text(
            as_list(
                "Режим управления абонементом",
                "/cancel - завершить работу с абонементом",
            )
        ).as_kwargs(),
    )


# Cancel command for Abonement
@router.message(
    StateFilter(MainGroup.abonement_mode),
    (or_f(Command("cancel"), F.text == "Выход")),
)
async def process_abonement_cancel_command(
    message: Message, state: FSMContext, user_type: list[str]
) -> None:
    logger.info(f"FSM: abonement: cancel command")
    await state.clear()
    await message.answer(
        text="Завершение работы с абонементами. Вы в главном меню.",
        reply_markup=kb.get_main_kb(user_type),
    )


# Cancel command for Abonement OPERATION mode
@router.message(
    StateFilter(AbonementGroup),
    (or_f(Command("cancel"), F.text == "Выход")),
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
    user = await db.user_by_id(user_id)
    if not user:
        logger.warning(f"FSM: abonement: user {user_id} not found")
        return
    # Find my abonements
    my_abonements = await db.abonements_list_by_owner(user)
    my_abonements_list = [abonement.name for abonement in my_abonements]
    my_abonements_text = None
    if my_abonements_list:
        my_abonements_text = Text(
            as_list(
                Bold("Мои абонементы:"),
                as_marked_list(*my_abonements_list, marker="👤 "),
            )
        )
    # Find other abonements
    other_abonements = await db.abonements_list_by_user(user)
    other_abonements_list = [abonement.name for abonement in other_abonements]
    other_abonements_text = None
    if other_abonements_list:
        other_abonements_text = Text(
            as_list(
                Bold("Абонементы друзей:"),
                as_marked_list(*other_abonements_list, marker="👥 "),
            )
        )
    # Combine abonements info
    if my_abonements_text or other_abonements_text:
        await message.answer(
            f"Доступно абонементов: {len(my_abonements) + len(other_abonements)}",
            reply_markup=kb.no_keyboard,
        )
        await message.answer(
            **as_list(
                *my_abonements_text if my_abonements_text else [],
                *other_abonements_text if other_abonements_text else [],
                Bold("С каким абонементом работаем?"),
                "/cancel - завершить работу с абонементами",
            ).as_kwargs(),
            reply_markup=kb.get_abonement_list_kb(my_abonements, other_abonements),
        )
    else:
        await message.answer(
            "Абонементов нет. Создайте новый или присоединитесь к существующему."
        )


#
# Add new Abonement: BEGIN
#
@router.message(
    StateFilter(MainGroup.abonement_mode), F.text == "Создать новый абонемент"
)
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
            "/cancel - отменить операцию с абонементом",
        ).as_kwargs(),
    )


# Add new Abonement: WRONG ABONEMENT NAME
@router.message(StateFilter(AbonementGroup.abonement_name))
async def process_wrong_name_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG NAME for abonement")
    await message.answer(
        **as_list(
            "Имя не подходит. Нужен просто текст.",
            "",
            "Попробуйте другое имя, без спецсимволов.",
            "/cancel - отменить операцию с абонементом",
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
            "/cancel - отменить операцию с абонементом",
        ).as_kwargs()
    )


# Add new Abonement: WRONG ABONEMENT TOTAL PASSES
@router.message(StateFilter(AbonementGroup.abonement_total_passes))
async def process_wrong_passes_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG TOTAL PASSES for abonement")
    await message.answer(
        **as_list(
            "Количество посещений не подходит.",
            "",
            "Попробуйте отправить положительное число или 0.",
            "/cancel - отменить операцию с абонементом",
        ).as_kwargs()
    )


# Add new Abonement: GOOD ABONEMENT DESCRIPTION
@router.message(
    StateFilter(AbonementGroup.abonement_description),
    or_f(Command("skip"), F.text),
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
    user = await db.user_by_id(user_id)
    abonement_name = (await state.get_data()).get("name")
    total_passes = (await state.get_data()).get("total_passes")
    description = (await state.get_data()).get("description")
    abonement_id = (await state.get_data()).get("abonement_id")
    if not user or not abonement_name or total_passes is None:
        logger.warning(f"FSM: abonement: user {user_id} not found or wrong state")
        return
    if abonement_id:
        abonement = await db.abonement_edit(
            abonement_id=abonement_id,
            name=abonement_name,
            owner=user,
            total_passes=total_passes,
            description=description,
        )
        if abonement:
            logger.info(f"Updated abonement {abonement.id}")
        else:
            logger.warning(
                f"FSM: abonement: can't update abonement {abonement_id} for user {user_id}"
            )
    else:
        abonement = await db.abonement_create(
            name=abonement_name,
            owner=user,
            total_passes=total_passes,
            description=description,
        )
        if abonement:
            logger.info(f"Created new abonement {abonement.id}")
        else:
            logger.warning(f"FSM: abonement: can't create new abonement")
    # Reset state to Abonenment mode
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    if not abonement:
        return
    # Show info about abonement
    key = abonement.token
    if abonement_id:
        await message.answer(
            **as_list(
                "Абонемент изменён",
                as_key_value("Новое название", abonement.name),
                as_key_value(
                    "Новое описание",
                    (
                        abonement.description
                        if abonement.description
                        else Italic("отсутствует")
                    ),
                ),
                as_key_value(
                    "Всего посещений",
                    (
                        abonement.total_passes
                        if abonement.total_passes
                        else Italic("без ограничения")
                    ),
                ),
                as_key_value("Ключ", Code(key)),
            ).as_kwargs()
        )
    else:
        await message.answer(
            **as_list(
                "Абонемент создан:",
                Bold(abonement.name),
                "",
                "Ключ",
                Code(key),
                "",
                "Ссылка для подключения:",
                (
                    await create_start_link(bot=message.bot, payload=f"abonement_{key}")
                    if message.bot
                    else Bold("недоступна")
                ),
                "",
                "Если хотите поделиться абонементом, перешлите это сообщение другому пользователю.",
            ).as_kwargs()
        )
    await message.answer(
        **as_list(
            "Вы в меню работы с абонементами.",
            "/cancel - выйти в главное меню",
        ).as_kwargs(),
        reply_markup=kb.get_abonement_kb(),
    )


# Add new Abonement: WRONG ABONEMENT DESCRIPTION
@router.message(StateFilter(AbonementGroup.abonement_description))
async def process_wrong_description_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG description for abonement")
    await message.answer(
        **as_list(
            "Описание абонемента не подходит.",
            "",
            "/skip - не заполнять описание абонемента",
            "/cancel - отменить создание абонемента",
        ).as_kwargs()
    )


#
# Abonement join: BEGIN
#
@router.message(
    StateFilter(MainGroup.abonement_mode), F.text == "Присоединиться к абонементу"
)
async def process_join_abonement_command(message: Message, state: FSMContext) -> None:
    logger.info(f"FSM: abonement: BEGIN join abonement")
    await state.set_state(AbonementGroup.abonement_join)
    await message.answer(
        **as_list(
            "Подключаем существующий абонемент.",
            "",
            Bold("Введите ключ абонемента"),
            "/cancel - отменить подключение к абонементу",
        ).as_kwargs(),
        reply_markup=kb.no_keyboard,
    )


# Abonement join: GOOD key
@router.message(StateFilter(AbonementGroup.abonement_join), F.text)
async def process_good_key_join_abonement_command(
    message: Message, state: FSMContext, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: GOOD key for join abonement")
    # Check token
    abonement_token = message.text.lower() if message.text else None
    if not abonement_token or not re.search(
        r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
        abonement_token,
    ):
        await message.answer(
            **as_list(
                "Неверный формат ключа абонемента.",
                "Должно быть так:",
                Bold("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"),
                "",
                "Введите другой ключ.",
                "/cancel - отменить подключение к абонементу",
            ).as_kwargs()
        )
        return
    # Token accepted. Find abonement by token
    await state.update_data(abonement_token=abonement_token)
    await state.update_data(user_id=user_id)
    abonement = await db.abonement_by_token(abonement_token)
    if not abonement:
        await message.answer(
            **as_list(
                "Неверный ключ абонемента.",
                "Подходящих абонементов с таким ключом нет.",
                "",
                "Введите другой ключ.",
                "/cancel - отменить подключение к абонементу",
            ).as_kwargs()
        )
        return
    # Abonement found. Check if abonement is active
    if abonement.hidden:
        await message.answer(
            **as_list(
                "Этот абонемент был удален.",
                "",
                "Введите другой ключ.",
                "/cancel - отменить подключение к абонементу",
            ).as_kwargs()
        )
        return
    # Abonement good. Check user is not owner
    if abonement.owner_id == user_id:
        await message.answer(
            **as_list(
                "Вы не можете присоединиться к своему абонементу.",
                "",
                "Введите другой ключ.",
                "/cancel - отменить подключение к абонементу",
            ).as_kwargs()
        )
        return
    # User ok. Check user is not already in abonement
    abonement_user = await db.abonement_user(user_id=user_id, abonement_id=abonement.id)
    if abonement_user:
        await message.answer(
            **as_list(
                "Вы уже присоединены к этому абонементу.",
                Bold(abonement.name),
                "Он есть в списке ваших абонементов.",
                "",
                "Введите другой ключ.",
                "/cancel - отменить подключение к абонементу",
            ).as_kwargs()
        )
        return
    # It's first time - ok. Ask to add user to abonement
    await state.update_data(abonement_id=abonement.id)
    await state.set_state(AbonementGroup.abonement_accept)
    await message.answer(
        **as_list(
            "Вы хотите присоединиться к абонементу?",
            Bold(abonement.name),
            "",
            "/cancel - отменить подключение к абонементу",
        ).as_kwargs(),
        reply_markup=kb.yes_no_keyboard,
    )


# Abonement join: WRONG key
@router.message(StateFilter(AbonementGroup.abonement_join))
async def process_wrong_key_join_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG key for join abonement")
    await message.answer(
        **as_list(
            "Нужен ключ абонемента. Строка в формате:",
            Bold("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"),
            "",
            "/cancel - отменить подключение к абонементу",
        ).as_kwargs()
    )


# Abonement join: GOOD accept answer
@router.message(StateFilter(AbonementGroup.abonement_accept), F.text.in_({"Да", "Нет"}))
async def process_good_accept_join_abonement_command(
    message: Message, state: FSMContext, db: Database
) -> None:
    logger.info(f"FSM: abonement: GOOD accept answer for join abonement")
    data = await state.get_data()
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    if message.text == "Нет":
        await message.answer(
            **as_list(
                "Не присоединились к абонементу.",
                "",
                "Вы в меню работы с абонементами.",
                "/cancel - выйти в главное меню",
            ).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
        )
        return
    # Add user to abonement
    user_id = data.get("user_id")
    abonement_id = data.get("abonement_id")
    abonement_token = data.get("abonement_token")
    if not user_id or not abonement_id or not abonement_token:
        logger.warning(f"FSM: abonement: wrong state")
        return
    await db.abonement_user_add(
        user_id=user_id,
        abonement_id=abonement_id,
        abonement_token=abonement_token,
    )
    await message.answer(
        **as_list(
            "Присоединились к абонементу.",
            "Теперь он в списке ваших абонементов.",
            "",
            "Вы в меню работы с абонементами.",
            "/cancel - выйти в главное меню",
        ).as_kwargs(),
        reply_markup=kb.get_abonement_kb(),
    )


# Abonement join: WRONG accept answer
@router.message(StateFilter(AbonementGroup.abonement_accept))
async def process_wrong_accept_join_abonement_command(message: Message) -> None:
    logger.info(f"FSM: abonement: WRONG accept answer for join abonement")
    await message.answer(
        **as_list(
            "Неверный ответ. Только Да или Нет.",
            "",
            "/cancel - отменить подключение к абонементу",
        ).as_kwargs()
    )


# Abonement delete: got answer
@router.message(StateFilter(AbonementGroup.abonement_delete))
async def process_good_delete_abonement_command(
    message: Message, state: FSMContext, user_id: int, db: Database
) -> None:
    logger.info(f"FSM: abonement: GOOD delete answer for abonement")
    data = await state.get_data()
    await state.clear()
    await state.set_state(MainGroup.abonement_mode)
    abonement_id = data.get("abonement_id")
    abonement_key = data.get("abonement_key")
    operation = data.get("operation")
    if message.text and message.text.strip().lower() == "да" and abonement_id:
        result = await db.abonement_delete(abonement_id=abonement_id, user_id=user_id)
        await message.answer(
            **as_list(
                Text(
                    "Абонемент",
                    Bold(" не") if not result else "",
                    " удален" if operation == "delete" else " отключен",
                ),
                "",
                as_key_value(
                    "Ключ",
                    Code(abonement_key) if abonement_key else Italic("неизвестен"),
                ),
                "",
                "Вы в меню работы с абонементами.",
                "/cancel - выйти в главное меню",
            ).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
        )
    else:
        await message.answer(
            **as_list(
                "Абонемент не удален.",
                "",
                "Вы в меню работы с абонементами.",
                "/cancel - выйти в главное меню",
            ).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
        )


# Unknown command for Abonement
@router.message(StateFilter(MainGroup.abonement_mode))
async def process_abonement_unknown_command(message: Message) -> None:
    await message.answer(
        **as_list(
            "Неизвестная команда работы с абонементами.",
            "Справка - /help",
            "Выход - /cancel",
        ).as_kwargs()
    )
