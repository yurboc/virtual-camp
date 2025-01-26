import logging
import keyboards.common as kb
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Text, Bold, Italic, TextLink, as_list, as_key_value
from aiogram.utils.deep_linking import create_start_link
from const.states import MainGroup, AbonementGroup
from keyboards.common import AbonementCallbackFactory
from storage.db_api import Database
from utils import queue
from utils.config import config
from const.text import (
    msg,
    ab_info,
    ab_page,
    ab_del_ask,
    ab_del_visit_ask,
    date_h_m_fmt,
    date_fmt,
)

logger = logging.getLogger(__name__)
router = Router(name=__name__)


# Enter to Abonement
@router.callback_query(
    or_f(
        StateFilter(MainGroup.abonement_mode),
        StateFilter(AbonementGroup.open),
    ),
    AbonementCallbackFactory.filter(F.action == "open"),
)
async def callbacks_abonement_open(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement entering: %s", callback_data.id)
    await callback.answer()
    await state.update_data(
        {"offset": 0, "limit": config["BOT"]["ABONEMENTS"]["PAGINATION_LIMIT"]}
    )
    await state.set_state(AbonementGroup.open)
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or abonement.token != callback_data.token or not user:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    notify = await db.settings_value(user.id, "notify_abonement_%s" % abonement.id)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(None)
        visits_count = await db.abonement_visits_count(abonement.id)
        my_visits_count = await db.abonement_visits_count(abonement.id, user_id=user.id)
        await callback.message.answer(
            **ab_info(
                abonement.name,
                abonement.description,
                abonement.expiry_date,
                abonement.total_visits,
                visits_count,
                my_visits_count,
                notify,
            ).as_kwargs(),
            reply_markup=kb.get_abonement_control_kb(abonement, user.id, notify),
        )


# Exit from Abonement
@router.callback_query(
    StateFilter(AbonementGroup), AbonementCallbackFactory.filter(F.action == "exit")
)
async def callbacks_abonement_reject_visit(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement exiting: %s", callback_data.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    if not abonement or abonement.token != callback_data.token:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(None)
        await state.set_state(MainGroup.abonement_mode)
        await callback.message.answer(
            msg["abonement_main"],
            reply_markup=kb.get_abonement_kb(),
        )


# Ask to visit Abonement
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action == "ask_visit"),
)
async def callbacks_abonement_ask_visit(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement visit ask: %s", callback_data.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    if not abonement or abonement.token != callback_data.token:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(None)
        await state.set_state(AbonementGroup.visit)
        result = [msg["ab_visit_ask"], Bold(abonement.name), msg["ab_visit_confirm"]]
        await callback.message.answer(
            **as_list(*result).as_kwargs(),
            reply_markup=kb.get_abonement_yes_no_kb(abonement),
        )


# Visit Abonement
@router.callback_query(
    StateFilter(AbonementGroup.visit),
    AbonementCallbackFactory.filter(F.action.in_(["yes", "no"])),
)
async def callbacks_abonement_accept_visit(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement visit confirm: %s", callback_data.id)
    await callback.answer()
    await state.set_state(MainGroup.abonement_mode)
    # Answer NO
    if callback_data.action == "no":
        logger.info("Abonement visit canceled: %s", callback_data.id)
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_reply_markup(None)
            await callback.message.answer(
                msg["ab_no_visit"], reply_markup=kb.get_abonement_kb()
            )
        return
    # Answer YES
    logger.info("Abonement visit accepted: %s", callback_data.id)
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or abonement.token != callback_data.token or not user:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    abonement_visit = await db.abonement_visit_add(abonement.id, user.id)
    if callback.message and isinstance(callback.message, Message):
        if abonement_visit:  # Visit DONE
            result = [msg["ab_visit"], Bold(abonement_visit.ts.strftime(date_h_m_fmt))]
            queue.publish_result(
                {
                    "job_type": "abonement_visit",
                    "msg_type": "visit_new",
                    "abonement_id": abonement.id,
                    "visit_id": abonement_visit.id,
                    "visit_user_id": abonement_visit.user_id,
                    "user_id": user.id,
                    "ts": abonement_visit.ts.strftime(date_h_m_fmt),
                }
            )
        else:  # Visit FAILED (Abonement empty or deleted)
            result = [msg["ab_no_visit"], Bold(msg["ab_empty"])]
        await callback.message.edit_reply_markup(None)
        await callback.message.answer(
            **as_list(*result).as_kwargs(), reply_markup=kb.get_abonement_kb()
        )


# History of Abonement
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action.in_(["history", "prev", "next"])),
)
async def callbacks_abonement_visits(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement history: %s", callback_data.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    if not abonement or abonement.token != callback_data.token:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and isinstance(callback.message, Message):
        # Calculate pagination
        total = await db.abonement_visits_count(abonement.id)
        limit = await state.get_value(
            "limit", config["BOT"]["ABONEMENTS"]["PAGINATION_LIMIT"]
        )
        offset = await state.get_value("offset", 0)
        action = callback_data.action
        logger.info("Abonement history %s: %s, %s, %s", action, total, limit, offset)
        if action == "prev":
            if offset == 0:
                return
            if offset > limit:
                offset -= limit
            else:
                offset = 0
        elif action == "next":
            if offset + limit >= total:
                return
            offset += limit
        await state.update_data({"offset": offset, "limit": limit})
        await callback.message.edit_reply_markup(None)
        # Get visits for current page
        visits_list = await db.abonement_visits_list(
            abonement.id, limit=limit, offset=offset
        )
        visits_text = []
        # Generate one line for each visit
        for visit in visits_list:
            visits_text += [
                Text(
                    visit.ts.strftime(date_h_m_fmt),
                    " ",
                    TextLink(visit.user.name, url=f"tg://user?id={visit.user.tg_id}"),
                    (
                        Text(f" (@{visit.user.tg_username})")
                        if visit.user.tg_username
                        else ""
                    ),
                ),
            ]
        answer = as_list(ab_page(offset, total, len(visits_text)), *(visits_text))
        if callback_data.action in ["prev", "next"]:
            # Update message for << and >> buttons only
            await callback.message.edit_text(
                **answer.as_kwargs(),
                reply_markup=kb.get_abonement_history_kb(
                    abonement, offset, limit, total
                ),
            )
        else:
            # Create new message for all other buttons
            await callback.message.answer(
                **answer.as_kwargs(),
                reply_markup=kb.get_abonement_history_kb(
                    abonement, offset, limit, total
                ),
            )


# History of Abonement -- select Visit to EDIT or DELETE
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action.in_(["visit_edit", "visit_delete"])),
)
async def callbacks_abonement_edit_delete_select_visits(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement history edit/delete: %s", callback_data.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    if not abonement or abonement.token != callback_data.token:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and isinstance(callback.message, Message):
        # Calculate pagination
        total = await db.abonement_visits_count(abonement.id)
        limit = await state.get_value(
            "limit", config["BOT"]["ABONEMENTS"]["PAGINATION_LIMIT"]
        )
        offset = await state.get_value("offset", 0)
        action = callback_data.action
        # Get visits for current page
        logger.info("Abonement history %s: %s, %s, %s", action, total, limit, offset)
        visits_text = []
        if action == "visit_edit":
            await state.set_state(AbonementGroup.visit_edit)
            visits_text = [Text(msg["ab_visit_edit"]), Text(msg["ab_visit_select"])]
        elif action == "visit_delete":
            await state.set_state(AbonementGroup.visit_delete)
            visits_text = [Text(msg["ab_visit_delete"]), Text(msg["ab_visit_select"])]
        else:
            logger.error("Unknown action: %s", action)
            return
        # Create message
        answer = as_list(*(visits_text))
        visits_list = await db.abonement_visits_list(abonement.id, limit, offset)
        await callback.message.edit_reply_markup(None)
        await callback.message.answer(
            **answer.as_kwargs(),
            reply_markup=kb.get_abonement_visits_kb(abonement, visits_list, action),
        )


# History of Abonement -- confirm EDIT or DELETE of Visit
@router.callback_query(
    StateFilter(AbonementGroup.visit_edit, AbonementGroup.visit_delete),
    AbonementCallbackFactory.filter(),
)
async def callbacks_abonement_edit_delete_confirm_visits(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Visit edit/delete ask: %s %s", callback_data.id, callback_data.action)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    act_parts = callback_data.action.split("_")
    if (
        len(act_parts) != 3
        or act_parts[0] != "visit"
        or act_parts[1] not in ["edit", "delete"]
        or not abonement
        or not int(act_parts[2])
        or not user
    ):
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    # Get operation parameters
    action = act_parts[1]
    visit_id = int(act_parts[2])
    visit = await db.abonement_visit_get(visit_id)
    if not visit:
        logger.warning("Visit not found: %s", visit_id)
        return
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(None)
        is_abonement_owner = user.id == abonement.owner_id
        is_visit_owner = user.id == visit.user_id
        # Check permissions
        if not is_abonement_owner and not is_visit_owner:
            logger.info("Visit %s not owned by user", visit_id)
            await state.set_state(MainGroup.abonement_mode)
            await callback.message.answer(
                msg["ab_visit_not_owner"], reply_markup=kb.get_abonement_kb()
            )
            return
        # Save operation parameters
        await state.update_data({"visit_id": visit.id})
        # Process operation
        if action == "edit":
            logger.info("Visit edit: %s", visit_id)
            await state.set_state(AbonementGroup.visit_edit_confirm)
            await callback.message.answer(
                **as_list(
                    as_key_value(msg["ab_visit_date"], visit.ts.strftime(date_h_m_fmt)),
                    Text(msg["ab_visit_new_date"], " ", msg["date_time_format"]),
                    Text(msg["cancel"]),
                ).as_kwargs(),
                reply_markup=kb.empty_kb,
            )
        elif action == "delete":
            logger.info("Visit delete: %s", visit_id)
            await state.set_state(AbonementGroup.visit_delete_confirm)
            await callback.message.answer(
                **ab_del_visit_ask().as_kwargs(), reply_markup=kb.empty_kb
            )


# Share Abonement
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action == "share"),
)
async def callbacks_abonement_share(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement sharing: %s", callback_data.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    if not abonement or abonement.token != callback_data.token:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(None)
        await state.set_state(MainGroup.abonement_mode)
        if not abonement.spreadsheet_id:
            queue.publish_result(
                {
                    "job_type": "abonement_update",
                    "abonement_id": abonement.id,
                    "user_tg_id": callback.from_user.id,
                }
            )
        await callback.message.answer(
            **as_list(
                msg["ab_title"],
                Bold(abonement.name),
                *[Italic(abonement.description), ""] if abonement.description else "",
                msg["ab_link"],
                (
                    await create_start_link(
                        bot=callback.message.bot, payload=f"abonement_{abonement.token}"
                    )
                    if callback.message.bot
                    else Bold(msg["unavailable"])
                ),
                msg["ab_sheets"],
                (
                    config["GOOGLE"]["DRIVE"]["LINK_TEMPLATE"].format(
                        abonement.spreadsheet_id
                    )
                    if abonement.spreadsheet_id
                    else Bold(msg["unavailable"])
                ),
            ).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
        )


# Edit Abonement
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action == "edit"),
)
async def callbacks_abonement_edit(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement editing: %s", callback_data.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if (
        not abonement
        or abonement.token != callback_data.token
        or not user
        or user.id != abonement.owner_id
    ):
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(None)
        await state.update_data(
            {
                "abonement_id": abonement.id,
                "name": abonement.name,
                "description": abonement.description,
                "expiry_date": (
                    abonement.expiry_date.isoformat() if abonement.expiry_date else None
                ),
                "total_visits": abonement.total_visits,
            }
        )
        await state.set_state(AbonementGroup.name)
        # Ask new Abonement name
        await callback.message.answer(
            **Text(
                as_list(
                    msg["ab_edit_begin"],
                    "",
                    msg["ab_name_label"],
                    Bold(abonement.name),
                    "",
                    msg["ab_descr_label"],
                    Italic(
                        abonement.description if abonement.description else msg["none"]
                    ),
                    "",
                    msg["ab_expiry_date_label"],
                    Bold(
                        abonement.expiry_date.strftime(date_fmt)
                        if abonement.expiry_date
                        else msg["ab_unlim"]
                    ),
                    "",
                    msg["ab_visits_label"],
                    Bold(
                        abonement.total_visits
                        if abonement.total_visits
                        else msg["ab_unlim"]
                    ),
                    "",
                    Bold(msg["ab_edit_name"]),
                    msg["skip"],
                    msg["cancel"],
                )
            ).as_kwargs(),
            reply_markup=kb.empty_kb,
        )


# Delete or Unlink Abonement
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action == "delete"),
)
async def callbacks_abonement_delete(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement deleting: %s", callback_data.id)
    logger.info("Abonement token: %s", callback_data.token)
    logger.info("Abonement owner: %s", callback.from_user.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or abonement.token != callback_data.token or not user:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(None)
        await state.update_data(
            {
                "abonement_id": abonement.id,
                "abonement_key": abonement.token,
                "operation": "delete" if user.id == abonement.owner_id else "unlink",
            }
        )
        await state.set_state(AbonementGroup.delete)
        await callback.message.answer(
            **ab_del_ask(user.id == abonement.owner_id, abonement.name).as_kwargs(),
            reply_markup=kb.empty_kb,
        )


# Abonement Notifications
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action.in_(["notify_on", "notify_off"])),
)
async def callbacks_abonement_notify(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement notifications: %s", callback_data.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or not user:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer(msg["ab_failure_callback"])
        return
    notify = await db.settings_value(user.id, "notify_abonement_%s" % abonement.id)
    if callback_data.action == "notify_on" and (notify == "off" or not notify):
        await db.settings_set(user.id, "notify_abonement_%s" % abonement.id, "all")
        notify = "all"
    elif callback_data.action == "notify_off" and notify == "all":
        await db.settings_set(user.id, "notify_abonement_%s" % abonement.id, "off")
        notify = "off"
    logger.info("Abonement notify: %s", notify)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(None)
        if notify and notify == "all":
            notify_text = msg["notify_on"]
        else:
            notify_text = msg["notify_off"]
        await callback.message.answer(
            **as_list(Bold(abonement.name), notify_text).as_kwargs(),
            reply_markup=kb.get_abonement_control_kb(abonement, user.id, notify),
        )
