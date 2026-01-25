import asyncio
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import asyncpg
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)
from dotenv import load_dotenv
from mcrcon import MCRcon
from bot.texts import Locale


logging.basicConfig(level=logging.INFO)


@dataclass
class RconConfig:
    host: str
    port: int
    password: str


@dataclass
class AppConfig:
    admin_chat_id: int
    admin_ids: List[int]
    migrations_dir: Path
    rcon: RconConfig
    db_dsn: str
    locale: Locale


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


class RequestState(StatesGroup):
    waiting_comment = State()


def parse_admin_ids(value: str) -> List[int]:
    if not value:
        return []
    ids: List[int] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            ids.append(int(raw))
        except ValueError:
            logging.warning("Skipped admin id that is not a number: %s", raw)
    return ids


async def apply_migrations(pool: asyncpg.Pool, migrations_dir: Path) -> None:
    if not migrations_dir.exists():
        logging.warning("Migrations directory %s does not exist, skipping", migrations_dir)
        return

    for path in sorted(migrations_dir.glob("*.sql")):
        sql = path.read_text()
        logging.info("Applying migration %s", path.name)
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(sql)


async def create_request(pool: asyncpg.Pool, user_id: int, chat_id: int, username: str, comment: Optional[str]) -> int:
    query = """
        INSERT INTO whitelist_requests (user_id, chat_id, username, comment)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """
    async with pool.acquire() as conn:
        record = await conn.fetchrow(query, user_id, chat_id, username, comment)
        return int(record["id"])


async def fetch_request(pool: asyncpg.Pool, request_id: int) -> Optional[asyncpg.Record]:
    query = "SELECT * FROM whitelist_requests WHERE id = $1"
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, request_id)


async def mark_request(pool: asyncpg.Pool, request_id: int, status: str, decided_by: int) -> None:
    query = """
        UPDATE whitelist_requests
        SET status = $2, decided_at = NOW(), decided_by = $3
        WHERE id = $1
    """
    async with pool.acquire() as conn:
        await conn.execute(query, request_id, status, decided_by)


async def fetch_usernames(pool: asyncpg.Pool, user_id: int) -> List[asyncpg.Record]:
    query = """
        SELECT username, decided_at
        FROM whitelist_requests
        WHERE user_id = $1 AND status = 'approved'
        ORDER BY decided_at DESC NULLS LAST, created_at DESC
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, user_id)


async def fetch_user_by_mc_username(pool: asyncpg.Pool, mc_username: str) -> Optional[int]:
    query = """
        SELECT user_id
        FROM whitelist_requests
        WHERE username = $1 AND status = 'approved'
        ORDER BY decided_at DESC NULLS LAST, created_at DESC
        LIMIT 1
    """
    async with pool.acquire() as conn:
        record = await conn.fetchrow(query, mc_username)
        if not record:
            return None
        return int(record["user_id"])


def whitelist_player(config: RconConfig, username: str) -> str:
    try:
        with MCRcon(config.host, config.password, port=config.port) as client:
            return client.command(f"whitelist add {username}")
    except Exception as exc:  # noqa: BLE001
        logging.exception("RCON whitelist command failed")
        raise RuntimeError("Failed to whitelist player via RCON") from exc


def build_admin_keyboard(request_id: int, locale: Locale, user_id: int) -> InlineKeyboardMarkup:
    approve = InlineKeyboardButton(text=locale.t("approve_button"), callback_data=f"approve:{request_id}")
    deny = InlineKeyboardButton(text=locale.t("deny_button"), callback_data=f"deny:{request_id}")
    profile = InlineKeyboardButton(text=locale.t("profile_button"), url=f"tg://user?id={user_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[approve, deny], [profile]])


def build_skip_keyboard(locale: Locale) -> InlineKeyboardMarkup:
    skip = InlineKeyboardButton(text=locale.t("skip_button"), callback_data="skip_comment")
    return InlineKeyboardMarkup(inline_keyboard=[[skip]])


def format_user(user: types.User) -> str:
    if user.username:
        return f"@{user.username}"
    return f'<a href="tg://user?id={user.id}">{user.full_name}</a>'


async def main() -> None:
    load_dotenv()

    bot_token = os.environ.get("BOT_TOKEN")
    admin_chat_id_raw = os.environ.get("ADMIN_CHAT_ID")
    admin_ids_raw = os.environ.get("ADMIN_IDS", "")
    locale_name = os.environ.get("LOCALE", "en").lower()
    db_dsn = os.environ.get("DATABASE_URL") or (
        "postgresql://{user}:{password}@{host}:{port}/{database}".format(
            user=os.environ.get("POSTGRES_USER", "mcwhitelist"),
            password=os.environ.get("POSTGRES_PASSWORD", "mcwhitelist"),
            host=os.environ.get("POSTGRES_HOST", "db"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            database=os.environ.get("POSTGRES_DB", "mcwhitelist"),
        )
    )

    rcon_config = RconConfig(
        host=os.environ.get("RCON_HOST", "localhost"),
        port=int(os.environ.get("RCON_PORT", "25575")),
        password=os.environ.get("RCON_PASSWORD", ""),
    )
    migrations_dir = Path(os.environ.get("MIGRATIONS_DIR", "/app/schema"))

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required")
    if not admin_chat_id_raw:
        raise RuntimeError("ADMIN_CHAT_ID is required")

    admin_chat_id = int(admin_chat_id_raw)
    admin_ids = parse_admin_ids(admin_ids_raw)

    config = AppConfig(
        admin_chat_id=admin_chat_id,
        admin_ids=admin_ids,
        migrations_dir=migrations_dir,
        rcon=rcon_config,
        db_dsn=db_dsn,
        locale=Locale(locale_name),
    )

    bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    pool = await asyncpg.create_pool(dsn=config.db_dsn)

    await apply_migrations(pool, config.migrations_dir)
    logging.info("Migrations applied, starting bot")

    @dp.message(CommandStart())
    async def handle_start(message: Message) -> None:
        hint = config.locale.t("username_hint")
        await message.answer(config.locale.t("start", hint=hint))

    @dp.message(Command("whois"))
    async def handle_whois(message: Message) -> None:
        if message.chat.type == "private":
            return

        target_user: Optional[User] = None
        mc_username: Optional[str] = None
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
        elif message.entities:
            for entity in message.entities:
                if entity.type == "text_mention" and entity.user:
                    target_user = entity.user
                    break
        else:
            text = message.text or ""
            parts = text.split(maxsplit=1)
            arg_text = parts[1].strip() if len(parts) > 1 else ""
            if arg_text:
                token = arg_text.split()[0].lstrip("@")
                if token:
                    if USERNAME_RE.match(token):
                        mc_username = token
                    else:
                        try:
                            chat = await bot.get_chat(f"@{token}")
                        except Exception:
                            chat = None
                        if chat and chat.type == "private":
                            target_user = chat

        if mc_username:
            user_id = await fetch_user_by_mc_username(pool, mc_username)
            if not user_id:
                await message.reply("Игрок не имеет проходки или был добавлен не через меня, сорян")
                return
            await message.reply(f'<a href="tg://user?id={user_id}">Профиль</a>')
            return

        if not target_user:
            await message.reply("Игрок не имеет проходки или был добавлен не через меня, сорян")
            return

        records = await fetch_usernames(pool, target_user.id)
        if not records:
            await message.reply("Игрок не имеет проходки или был добавлен не через меня, сорян")
            return

        lines = []
        for record in records:
            decided_at = record["decided_at"]
            date_text = decided_at.strftime("%d.%m.%y") if decided_at else "??.??.??"
            lines.append(f"{date_text} - {record['username']}")
        await message.reply("\n".join(lines))

    @dp.message(StateFilter(None), F.text & ~F.via_bot)
    async def handle_username(message: Message, state: FSMContext) -> None:
        if message.chat.id != message.from_user.id:
            return

        username = message.text.strip()
        if not username:
            await message.answer(config.locale.t("username_hint"))
            return
        if not USERNAME_RE.match(username):
            await message.answer(config.locale.t("invalid_username"))
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
            config.locale.t("ask_comment"),
            reply_markup=build_skip_keyboard(config.locale),
        )

    async def finalize_request(source_message: Message, state: FSMContext, comment: Optional[str]) -> None:
        data = await state.get_data()
        username = data.get("username")
        user_id = data.get("user_id")
        chat_id = data.get("chat_id")
        full_name = data.get("full_name")
        mention = data.get("mention") or full_name or username
        if not username:
            await state.clear()
            await source_message.answer(config.locale.t("username_hint"))
            return
        if not user_id or not chat_id:
            await state.clear()
            await source_message.answer(config.locale.t("username_hint"))
            return

        request_id = await create_request(pool, int(user_id), int(chat_id), username, comment)

        await source_message.answer(config.locale.t("request_sent", request_id=request_id))

        admin_message = config.locale.t(
            "admin_request",
            request_id=request_id,
            full_name=full_name or username,
            tg_id=user_id,
            username=username,
        )
        comment_for_admin = comment or config.locale.t("no_comment")
        admin_message = f"{admin_message}\n{config.locale.t('admin_comment', comment=comment_for_admin)}"
        await bot.send_message(
            chat_id=config.admin_chat_id,
            text=admin_message,
            reply_markup=build_admin_keyboard(request_id, config.locale, int(user_id)),
        )
        await state.clear()

    @dp.message(RequestState.waiting_comment)
    async def handle_comment(message: Message, state: FSMContext) -> None:
        if message.chat.id != message.from_user.id:
            return

        comment_text = (message.text or "").strip()
        if comment_text.lower() == "skip":
            comment_text = ""
        await finalize_request(message, state, comment_text or None)

    @dp.callback_query(RequestState.waiting_comment, F.data == "skip_comment")
    async def skip_comment(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message and callback.message.chat.id != callback.from_user.id:
            await callback.answer(config.locale.t("private_only"), show_alert=True)
            return
        await callback.answer()
        if callback.message:
            await finalize_request(callback.message, state, None)
        else:
            await state.clear()

    @dp.callback_query(F.data.startswith("approve:") | F.data.startswith("deny:"))
    async def handle_decision(callback: CallbackQuery) -> None:
        action, _, id_raw = callback.data.partition(":")
        try:
            request_id = int(id_raw)
        except ValueError:
            await callback.answer(config.locale.t("invalid_request"), show_alert=True)
            return

        if callback.from_user.id not in config.admin_ids:
            await callback.answer(config.locale.t("not_allowed"), show_alert=True)
            return

        record = await fetch_request(pool, request_id)
        if not record:
            await callback.answer(config.locale.t("request_not_found"), show_alert=True)
            return

        if record["status"] != "pending":
            await callback.answer(config.locale.t("already_handled"), show_alert=True)
            return

        if action == "approve":
            try:
                whitelist_player(config.rcon, record["username"])
            except Exception:
                await callback.answer(config.locale.t("rcon_failed"), show_alert=True)
                return
            await mark_request(pool, request_id, "approved", callback.from_user.id)
            await callback.answer("Approved", show_alert=False)
            await bot.send_message(
                chat_id=record["chat_id"],
                text=config.locale.t("approved_user", request_id=request_id),
            )
            verdict_text = config.locale.t("admin_verdict_approved", admin=format_user(callback.from_user))
        else:
            await mark_request(pool, request_id, "denied", callback.from_user.id)
            await callback.answer("Denied", show_alert=False)
            await bot.send_message(
                chat_id=record["chat_id"],
                text=config.locale.t("denied_user", request_id=request_id),
            )
            verdict_text = config.locale.t("admin_verdict_denied", admin=format_user(callback.from_user))

        if callback.message:
            new_text = f"{callback.message.text}\n\n{verdict_text}"
            try:
                await callback.message.edit_text(new_text, reply_markup=None)
            except Exception:
                logging.exception("Failed to edit admin request message")

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
