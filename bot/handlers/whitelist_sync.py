from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.context import AppContext
from bot.services.whitelist import sync_whitelist


router = Router()


@router.message(Command("whitelist"))
async def handle_whitelist_sync(message: Message, context: AppContext) -> None:
    if message.from_user.id not in context.config.admin_ids:
        await message.reply(context.config.locale.t("not_allowed"))
        return

    await message.reply(context.config.locale.t("whitelist_cleanup_started"))
    removed = await sync_whitelist(context)

    if not removed:
        await message.reply(context.config.locale.t("whitelist_cleanup_none"))
        return

    await message.reply(context.config.locale.t("whitelist_cleanup_done", count=len(removed)))
    if len(removed) <= 50:
        await message.reply(context.config.locale.t("whitelist_cleanup_list", usernames=", ".join(removed)))
