import logging
from pathlib import Path
from typing import List, Optional

import asyncpg

logger = logging.getLogger(__name__)


async def apply_migrations(pool: asyncpg.Pool, migrations_dir: Path) -> None:
    if not migrations_dir.exists():
        logger.warning("Migrations directory %s does not exist, skipping", migrations_dir)
        return

    for path in sorted(migrations_dir.glob("*.sql")):
        sql = path.read_text()
        logger.info("Applying migration %s", path.name)
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(sql)


async def create_request(
    pool: asyncpg.Pool,
    user_id: int,
    chat_id: int,
    username: str,
    comment: Optional[str],
) -> int:
    query = """
        INSERT INTO whitelist_requests (user_id, chat_id, username, comment)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """
    logger.debug("SQL create_request: %s | params=%s", query.strip(), (user_id, chat_id, username, comment))
    async with pool.acquire() as conn:
        record = await conn.fetchrow(query, user_id, chat_id, username, comment)
        return int(record["id"])


async def fetch_request(pool: asyncpg.Pool, request_id: int) -> Optional[asyncpg.Record]:
    query = "SELECT * FROM whitelist_requests WHERE id = $1"
    logger.debug("SQL fetch_request: %s | params=%s", query, (request_id,))
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, request_id)


async def mark_request(pool: asyncpg.Pool, request_id: int, status: str, decided_by: int) -> None:
    query = """
        UPDATE whitelist_requests
        SET status = $2, decided_at = NOW(), decided_by = $3
        WHERE id = $1
    """
    logger.debug("SQL mark_request: %s | params=%s", query.strip(), (request_id, status, decided_by))
    async with pool.acquire() as conn:
        await conn.execute(query, request_id, status, decided_by)


async def fetch_usernames(pool: asyncpg.Pool, user_id: int) -> List[asyncpg.Record]:
    query = """
        SELECT username, decided_at, status
        FROM whitelist_requests
        WHERE user_id = $1
        ORDER BY decided_at DESC NULLS LAST, created_at DESC
    """
    logger.debug("SQL fetch_usernames: %s | params=%s", query.strip(), (user_id,))
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
    logger.debug("SQL fetch_user_by_mc_username: %s | params=%s", query.strip(), (mc_username,))
    async with pool.acquire() as conn:
        record = await conn.fetchrow(query, mc_username)
        if not record:
            return None
        return int(record["user_id"])


async def fetch_approved_usernames(pool: asyncpg.Pool) -> List[str]:
    query = """
        SELECT username
        FROM whitelist_requests
        WHERE status = 'approved'
    """
    logger.debug("SQL fetch_approved_usernames: %s", query.strip())
    async with pool.acquire() as conn:
        records = await conn.fetch(query)
        return [record["username"] for record in records]


async def fetch_approved_requests_by_user(pool: asyncpg.Pool, user_id: int) -> List[asyncpg.Record]:
    query = """
        SELECT id, user_id, username, decided_at, created_at
        FROM whitelist_requests
        WHERE user_id = $1 AND status = 'approved'
        ORDER BY decided_at DESC NULLS LAST, created_at DESC
    """
    logger.debug("SQL fetch_approved_requests_by_user: %s | params=%s", query.strip(), (user_id,))
    async with pool.acquire() as conn:
        return await conn.fetch(query, user_id)


async def fetch_approved_requests(pool: asyncpg.Pool) -> List[asyncpg.Record]:
    query = """
        SELECT id, user_id, username, decided_at, created_at
        FROM whitelist_requests
        WHERE status = 'approved'
        ORDER BY user_id, decided_at DESC NULLS LAST, created_at DESC
    """
    logger.debug("SQL fetch_approved_requests: %s", query.strip())
    async with pool.acquire() as conn:
        return await conn.fetch(query)


async def mark_request_status(pool: asyncpg.Pool, request_id: int, status: str, decided_by: int) -> None:
    query = """
        UPDATE whitelist_requests
        SET status = $2, decided_by = $3
        WHERE id = $1
    """
    logger.debug("SQL mark_request_status: %s | params=%s", query.strip(), (request_id, status, decided_by))
    async with pool.acquire() as conn:
        await conn.execute(query, request_id, status, decided_by)


async def delete_request(pool: asyncpg.Pool, request_id: int) -> None:
    query = "DELETE FROM whitelist_requests WHERE id = $1"
    logger.debug("SQL delete_request: %s | params=%s", query, (request_id,))
    async with pool.acquire() as conn:
        await conn.execute(query, request_id)
