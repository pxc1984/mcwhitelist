import asyncio
import logging

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from dotenv import load_dotenv

from bot.config import load_config
from bot.context import AppContext
from bot.db import apply_migrations
from bot.handlers import router as handlers_router


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def main() -> None:
    load_dotenv()
    config = load_config()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    pool = await asyncpg.create_pool(dsn=config.db_dsn)

    await apply_migrations(pool, config.migrations_dir)
    logger.info("Migrations applied, starting bot")

    context = AppContext(bot=bot, pool=pool, config=config)
    dp.include_router(handlers_router)

    await dp.start_polling(bot, context=context, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
