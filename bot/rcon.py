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


def remove_whitelist_player(config: RconConfig, username: str) -> str:
    try:
        with MCRcon(config.host, config.password, port=config.port) as client:
            return client.command(f"whitelist remove {username}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("RCON whitelist remove command failed")
        raise RuntimeError("Failed to remove player from whitelist via RCON") from exc


def list_whitelisted_players(config: RconConfig) -> list[str]:
    try:
        with MCRcon(config.host, config.password, port=config.port) as client:
            response = client.command("whitelist list")
    except Exception as exc:  # noqa: BLE001
        logger.exception("RCON whitelist list command failed")
        raise RuntimeError("Failed to fetch whitelist via RCON") from exc

    if ":" not in response:
        return []
    _, _, tail = response.partition(":")
    names = [name.strip() for name in tail.split(",")]
    return [name for name in names if name]
