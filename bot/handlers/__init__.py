from aiogram import Router

from bot.handlers import comment, decision, skip_comment, start, username, whois, whitelist_sync, manual


router = Router()
router.include_router(start.router)
router.include_router(whois.router)
router.include_router(username.router)
router.include_router(comment.router)
router.include_router(skip_comment.router)
router.include_router(decision.router)
router.include_router(whitelist_sync.router)
router.include_router(manual.router)
