from dataclasses import dataclass

import asyncpg
from aiogram import Bot

from bot.config import AppConfig


@dataclass
class AppContext:
    bot: Bot
    pool: asyncpg.Pool
    config: AppConfig
