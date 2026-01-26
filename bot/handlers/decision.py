import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.context import AppContext
from bot.db import fetch_request, mark_request
from bot.rcon import whitelist_player
from bot.utils import format_user

logger = logging.getLogger(__name__)


router = Router()


@router.callback_query(F.data.startswith("approve:") | F.data.startswith("deny:"))
async def handle_decision(callback: CallbackQuery, context: AppContext) -> None:
    action, _, id_raw = callback.data.partition(":")
    try:
        request_id = int(id_raw)
    except ValueError:
        await callback.answer(context.config.locale.t("invalid_request"), show_alert=True)
        return

    if callback.from_user.id not in context.config.admin_ids:
        await callback.answer(context.config.locale.t("not_allowed"), show_alert=True)
        return

    record = await fetch_request(context.pool, request_id)
    if not record:
        await callback.answer(context.config.locale.t("request_not_found"), show_alert=True)
        return

    if record["status"] != "pending":
        await callback.answer(context.config.locale.t("already_handled"), show_alert=True)
        return

    if action == "approve":
        try:
            whitelist_player(context.config.rcon, record["username"])
        except Exception:
            await callback.answer(context.config.locale.t("rcon_failed"), show_alert=True)
            return
        await mark_request(context.pool, request_id, "approved", callback.from_user.id)
        await callback.answer("Approved", show_alert=False)
        await context.bot.send_message(
            chat_id=record["chat_id"],
            text=context.config.locale.t("approved_user", request_id=request_id),
        )
        verdict_text = context.config.locale.t("admin_verdict_approved", admin=format_user(callback.from_user))
    else:
        await mark_request(context.pool, request_id, "denied", callback.from_user.id)
        await callback.answer("Denied", show_alert=False)
        await context.bot.send_message(
            chat_id=record["chat_id"],
            text=context.config.locale.t("denied_user", request_id=request_id),
        )
        verdict_text = context.config.locale.t("admin_verdict_denied", admin=format_user(callback.from_user))

    if callback.message:
        new_text = f"{callback.message.text}\n\n{verdict_text}"
        try:
            await callback.message.edit_text(new_text, reply_markup=None)
        except Exception:
            logger.exception("Failed to edit admin request message")
