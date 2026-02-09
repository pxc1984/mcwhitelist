import logging

from aiogram import Router, types
from aiogram.filters import CommandObject, Command

from bot import db, rcon
from bot.context import AppContext
from bot.utils import USERNAME_RE

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("add", "pustitt"))
async def add_user(message: types.Message, command: CommandObject, context: AppContext):
    if message.from_user.id not in context.config.admin_ids:
        await message.answer(context.config.locale.t("not_allowed"))
        return

    if not command.args:
        await message.answer(context.config.locale.t("add_user_usage"))
        return

    logger.debug("add user request from %d with args: %s", message.from_user.id, command.args)
    args = command.args.split(" ", 1)
    if len(args) != 2:
        await message.answer(context.config.locale.t("add_user_usage"))
        return
    try:
        tg_id, username = int(args[0]), args[1]
    except ValueError:
        await message.answer(context.config.locale.t("add_user_usage"))
        return

    if not USERNAME_RE.match(username):
        await message.answer(context.config.locale.t("invalid_username"))
        return

    request_id = await db.create_request(context.pool, tg_id, message.chat.id, username, None)
    await db.mark_request(context.pool, request_id, "approved", tg_id)
    rcon.whitelist_player(context.config.rcon, username)

    await message.reply(context.config.locale.t("add_user_success", username=username, tg_id=str(tg_id)))
    logger.info("User %s (TG: %d) added by admin %d", username, tg_id, message.from_user.id)
