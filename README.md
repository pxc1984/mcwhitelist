# Minecraft Whitelist Bot

Telegram bot (aiogram) that collects whitelist requests and lets admins approve them. Approved usernames are added to the Minecraft server via RCON. Runs with two containers: the bot and PostgreSQL.

## Setup
- Copy `.env.example` to `.env` and fill in:
  - `BOT_TOKEN`: Bot token from @BotFather.
  - `ADMIN_CHAT_ID`: Chat ID where requests are sent (a group or a DM).
  - `ADMIN_IDS`: Comma-separated Telegram user IDs that can approve/deny.
  - `LOCALE`: `en` (default) or `ru`.
  - `POSTGRES_*`: Database credentials (match compose defaults or your own).
  - `RCON_*`: Host/port/password for the Minecraft server RCON endpoint.
- Build and start: `docker compose up --build -d`
- The bot applies SQL migrations from `schema/` on startup.

## Usage
- Users DM the bot and send their Minecraft username (or just use `/start` and follow the prompt).
- Bot asks for optional comments for admins (reply text or type `skip`).
- The bot posts each request to `ADMIN_CHAT_ID` with Approve/Deny buttons.
- Admins approve to run `whitelist add <username>` over RCON and notify the user; deny sends a rejection message.

## Files
- `docker-compose.yml`: Bot + PostgreSQL stack.
- `bot/`: Bot source and Dockerfile.
- `schema/`: SQL migrations applied at startup.
- `.env.example`: Sample configuration.
