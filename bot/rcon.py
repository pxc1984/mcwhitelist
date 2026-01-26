import logging

from mcrcon import MCRcon

from bot.config import RconConfig

logger = logging.getLogger(__name__)


def whitelist_player(config: RconConfig, username: str) -> str:
    try:
        with MCRcon(config.host, config.password, port=config.port) as client:
            return client.command(f"whitelist add {username}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("RCON whitelist command failed")
        raise RuntimeError("Failed to whitelist player via RCON") from exc
