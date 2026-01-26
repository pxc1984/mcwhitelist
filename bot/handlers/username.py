from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.context import AppContext
from bot.keyboards import build_skip_keyboard
from bot.states import RequestState
from bot.utils import USERNAME_RE, format_user


router = Router()


@router.message(StateFilter(None), F.text & ~F.via_bot)
async def handle_username(message: Message, state: FSMContext, context: AppContext) -> None:
    if message.chat.id != message.from_user.id:
        return

    username = message.text.strip()
    if not username:
        await message.answer(context.config.locale.t("username_hint"))
        return
    if not USERNAME_RE.match(username):
        await message.answer(context.config.locale.t("invalid_username"))
        return

    await state.update_data(
        username=username,
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        full_name=message.from_user.full_name,
        mention=format_user(message.from_user),
    )
    await state.set_state(RequestState.waiting_comment)
    await message.answer(
        context.config.locale.t("ask_comment"),
        reply_markup=build_skip_keyboard(context.config.locale),
    )
