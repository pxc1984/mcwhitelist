from typing import Optional

from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.context import AppContext
from bot.db import create_request
from bot.keyboards import build_admin_keyboard


async def finalize_request(
    source_message: Message,
    state: FSMContext,
    comment: Optional[str],
    context: AppContext,
) -> None:
    data = await state.get_data()
    username = data.get("username")
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    full_name = data.get("full_name")
    mention = data.get("mention") or full_name or username
    if not username:
        await state.clear()
        await source_message.answer(context.config.locale.t("username_hint"))
        return
    if not user_id or not chat_id:
        await state.clear()
        await source_message.answer(context.config.locale.t("username_hint"))
        return

    request_id = await create_request(context.pool, int(user_id), int(chat_id), username, comment)

    await source_message.answer(context.config.locale.t("request_sent", request_id=request_id))

    admin_message = context.config.locale.t(
        "admin_request",
        request_id=request_id,
        mention=mention or full_name or username,
        tg_id=user_id,
        username=username,
    )
    comment_for_admin = comment or context.config.locale.t("no_comment")
    admin_message = f"{admin_message}\n{context.config.locale.t('admin_comment', comment=comment_for_admin)}"
    await context.bot.send_message(
        chat_id=context.config.admin_chat_id,
        text=admin_message,
        reply_markup=build_admin_keyboard(request_id, context.config.locale, int(user_id)),
    )
    await state.clear()
