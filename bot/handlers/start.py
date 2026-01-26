from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.context import AppContext


router = Router()


@router.message(CommandStart())
async def handle_start(message: Message, context: AppContext) -> None:
    hint = context.config.locale.t("username_hint")
    await message.answer(context.config.locale.t("start", hint=hint))
