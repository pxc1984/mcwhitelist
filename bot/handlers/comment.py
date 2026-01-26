from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.context import AppContext
from bot.services.requests import finalize_request
from bot.states import RequestState


router = Router()


@router.message(RequestState.waiting_comment)
async def handle_comment(message: Message, state: FSMContext, context: AppContext) -> None:
    if message.chat.id != message.from_user.id:
        return

    comment_text = (message.text or "").strip()
    if comment_text.lower() == "skip":
        comment_text = ""
    await finalize_request(message, state, comment_text or None, context)
