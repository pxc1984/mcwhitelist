from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.context import AppContext
from bot.services.requests import finalize_request
from bot.states import RequestState


router = Router()


@router.callback_query(RequestState.waiting_comment, F.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext, context: AppContext) -> None:
    if callback.message and callback.message.chat.id != callback.from_user.id:
        await callback.answer(context.config.locale.t("private_only"), show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await finalize_request(callback.message, state, None, context)
    else:
        await state.clear()
