import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from bot.texts import Locale


@dataclass
class RconConfig:
    host: str
    port: int
    password: str


@dataclass
class AppConfig:
    bot_token: str
    admin_chat_id: int
    admin_ids: List[int]
    migrations_dir: Path
    rcon: RconConfig
    db_dsn: str
    locale: Locale


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


def load_config() -> AppConfig:
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

    return AppConfig(
        bot_token=bot_token,
        admin_chat_id=admin_chat_id,
        admin_ids=admin_ids,
        migrations_dir=migrations_dir,
        rcon=rcon_config,
        db_dsn=db_dsn,
        locale=Locale(locale_name),
    )
