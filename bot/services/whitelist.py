import logging
from typing import Dict, Iterable, List, Optional, Set, Tuple

from bot.context import AppContext
from bot.db import (
    delete_request,
    fetch_approved_requests,
    fetch_approved_requests_by_user,
    fetch_approved_usernames,
)
from bot.rcon import list_whitelisted_players, remove_whitelist_player

logger = logging.getLogger(__name__)


def _pick_primary(records: List[dict], keep_username: Optional[str]) -> Tuple[Optional[dict], List[dict]]:
    if not records:
        return None, []
    if keep_username:
        for record in records:
            if record["username"] == keep_username:
                primary = record
                break
        else:
            primary = records[0]
    else:
        primary = records[0]
    secondary = [record for record in records if record["id"] != primary["id"]]
    return primary, secondary


async def cleanup_secondary_accounts(
    context: AppContext,
    user_id: Optional[int] = None,
    keep_username: Optional[str] = None,
) -> List[str]:
    removed: List[str] = []
    if user_id is not None:
        records = await fetch_approved_requests_by_user(context.pool, user_id)
        _, secondary = _pick_primary(records, keep_username)
        removed.extend(await _revoke_records(context, secondary))
        return removed

    records = await fetch_approved_requests(context.pool)
    grouped: Dict[int, List[dict]] = {}
    for record in records:
        grouped.setdefault(record["user_id"], []).append(record)

    for user_records in grouped.values():
        _, secondary = _pick_primary(user_records, None)
        removed.extend(await _revoke_records(context, secondary))

    return removed


async def _revoke_records(context: AppContext, records: Iterable[dict]) -> List[str]:
    removed: List[str] = []
    for record in records:
        username = record["username"]
        try:
            remove_whitelist_player(context.config.rcon, username)
        except Exception:
            logger.exception("Failed to remove username %s from whitelist", username)
        await delete_request(context.pool, record["id"])
        removed.append(username)
    return removed


async def sync_whitelist(context: AppContext) -> List[str]:
    removed_by_user = await cleanup_secondary_accounts(context)

    approved_usernames = await fetch_approved_usernames(context.pool)
    approved_lookup: Set[str] = {name.lower() for name in approved_usernames}

    server_names = list_whitelisted_players(context.config.rcon)
    removed_not_in_db: List[str] = []
    for name in server_names:
        if name.lower() not in approved_lookup:
            try:
                remove_whitelist_player(context.config.rcon, name)
                removed_not_in_db.append(name)
            except Exception:
                logger.exception("Failed to remove username %s from whitelist", name)

    return removed_by_user + removed_not_in_db
