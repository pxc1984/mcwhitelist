import logging
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, User

from bot.context import AppContext
from bot.db import fetch_user_by_mc_username, fetch_usernames
from bot.utils import USERNAME_RE

logger = logging.getLogger(__name__)


router = Router()


@router.message(Command("whois"))
async def handle_whois(message: Message, context: AppContext) -> None:
    if message.chat.type == "private":
        return

    logger.debug(
        "WHOIS request: chat_id=%s user_id=%s text=%s reply_to=%s",
        message.chat.id,
        message.from_user.id if message.from_user else None,
        message.text,
        bool(message.reply_to_message),
    )
    target_user: Optional[User] = None
    mc_username: Optional[str] = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        logger.debug("WHOIS target via reply: user_id=%s", target_user.id)
    if not target_user and message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                target_user = entity.user
                logger.debug("WHOIS target via text_mention: user_id=%s", target_user.id)
                break
    if not target_user:
        text = message.text or ""
        parts = text.split(maxsplit=1)
        arg_text = parts[1].strip() if len(parts) > 1 else ""
        if arg_text:
            token = arg_text.split()[0].lstrip("@")
            if token:
                if USERNAME_RE.match(token):
                    mc_username = token
                    logger.debug("WHOIS target via mc username: %s", mc_username)
                else:
                    try:
                        chat = await context.bot.get_chat(f"@{token}")
                    except Exception:
                        chat = None
                    if chat and chat.type == "private":
                        target_user = chat
                        logger.debug("WHOIS target via tg username: user_id=%s", target_user.id)

    if mc_username:
        user_id = await fetch_user_by_mc_username(context.pool, mc_username)
        if not user_id:
            logger.debug("WHOIS no user_id for mc username: %s", mc_username)
            await message.reply("Игрок не имеет проходки или был добавлен не через меня, сорян")
            return
        logger.debug("WHOIS found user_id=%s for mc username=%s", user_id, mc_username)
        await message.reply(f'<a href="tg://user?id={user_id}">Профиль</a>')
        return

    if not target_user:
        logger.debug("WHOIS no target resolved")
        await message.reply("Игрок не имеет проходки или был добавлен не через меня, сорян")
        return

    records = await fetch_usernames(context.pool, target_user.id)
    if not records:
        logger.debug("WHOIS no usernames for user_id=%s", target_user.id)
        await message.reply("Игрок не имеет проходки или был добавлен не через меня, сорян")
        return

    lines = []
    for record in records:
        decided_at = record["decided_at"]
        date_text = decided_at.strftime("%d.%m.%y") if decided_at else "??.??.??"
        lines.append(f"{date_text} - {record['username']} - {record['status']}")
    logger.debug("WHOIS result for user_id=%s: %s", target_user.id, lines)
    await message.reply("\n".join(lines))
