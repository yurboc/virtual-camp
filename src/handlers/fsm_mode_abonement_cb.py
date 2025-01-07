import logging
import keyboards.common as kb
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import (
    Text,
    Bold,
    Italic,
    TextLink,
    as_list,
    as_key_value,
)
from aiogram.utils.deep_linking import create_start_link
from const.states import MainGroup, AbonementGroup
from keyboards.common import AbonementCallbackFactory
from storage.db_api import Database
from utils.config import config
from const.text import cmd, msg, ab_info, ab_page, ab_del_ask, ab_date_fmt

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
    await state.set_data(
        {"offset": 0, "limit": config["BOT"]["ABONEMENTS"]["PAGINATION_LIMIT"]}
    )
    await state.set_state(AbonementGroup.open)
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or abonement.token != callback_data.token or not user:
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        visits_count = await db.abonement_visits_count(abonement.id)
        my_visits_count = await db.abonement_visits_count(abonement.id, user_id=user.id)
        await callback.message.answer(
            **ab_info(
                abonement.name,
                abonement.description,
                abonement.total_visits,
                visits_count,
                my_visits_count,
            ).as_kwargs(),
            reply_markup=kb.get_abonement_control_kb(abonement, user.id),
        )


# Exit from Abonement
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action == "exit"),
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
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_state(MainGroup.abonement_mode)
        await callback.message.answer(
            msg["ab_no_visit"],
            reply_markup=kb.get_abonement_kb(),
        )


# Visit Abonement
@router.callback_query(
    StateFilter(AbonementGroup.open),
    AbonementCallbackFactory.filter(F.action == "visit"),
)
async def callbacks_abonement_accept_visit(
    callback: CallbackQuery,
    callback_data: AbonementCallbackFactory,
    state: FSMContext,
    db: Database,
):
    logger.info("Abonement visiting: %s", callback_data.id)
    await callback.answer()
    abonement = await db.abonement_by_id(callback_data.id)
    user = await db.user_by_tg_id(callback.from_user.id)
    if not abonement or abonement.token != callback_data.token or not user:
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(msg["ab_failure_callback"])
        return
    abonement_visit = await db.abonement_visit_add(abonement.id, user.id)
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_state(MainGroup.abonement_mode)
        if abonement_visit:
            # Visit DONE
            result = [msg["ab_visit"], Bold(abonement_visit.ts.strftime(ab_date_fmt))]
        else:
            # Visit FAILED (Abonement empty or deleted)
            result = [msg["ab_no_visit"], Bold(msg["ab_empty"])]
        await callback.message.answer(
            **as_list(*result).as_kwargs(),
            reply_markup=kb.get_abonement_kb(),
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
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and type(callback.message) == Message:
        # Calculate pagination
        total = await db.abonement_visits_count(abonement.id)
        limit = (await state.get_data()).get(
            "limit", config["BOT"]["ABONEMENTS"]["PAGINATION_LIMIT"]
        )
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
        visits_list = await db.abonement_visits_list(
            abonement.id, limit=limit, offset=offset
        )
        visits_text = []
        # Generate one line for each visit
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
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_state(MainGroup.abonement_mode)
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
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(msg["ab_failure_callback"])
        return
    if callback.message and type(callback.message) == Message:
        await callback.message.edit_reply_markup(None)
        await state.set_data({"abonement_id": abonement.id})
        await state.set_state(AbonementGroup.name)
        # Ask new Abonement name
        await callback.message.answer(
            **Text(
                as_list(
                    msg["ab_edit_begin"],
                    Bold(abonement.name),
                    Italic(abonement.description if abonement.description else ""),
                    as_key_value(
                        msg["ab_total_visits"],
                        (
                            abonement.total_visits
                            if abonement.total_visits
                            else Italic(msg["ab_unlim_visits"])
                        ),
                    ),
                    "",
                    Bold(msg["ab_new_name"]),
                )
            ).as_kwargs(),
            reply_markup=kb.no_keyboard,
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
        if callback.message and type(callback.message) == Message:
            await callback.message.answer(msg["ab_failure_callback"])
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
        await state.set_state(AbonementGroup.delete)
        await callback.message.answer(
            **ab_del_ask(user.id == abonement.owner_id, abonement.name).as_kwargs(),
            reply_markup=kb.no_keyboard,
        )
