import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fluent.runtime import FluentLocalization, FluentResourceLoader
from .commandsworker import set_bot_commands
from .handlers import setup_routers
from .middlewares.l10n import L10nMiddleware
from .config import settings

async def main():
    
    logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )
    
    locales_path = Path(__file__).parent.joinpath("locales")
    l10n_loader = FluentResourceLoader(str(locales_path) + "/{locale}")
    l10n = FluentLocalization(
            ["ru"], 
            ["strings.ftl", "errors.ftl"], 
            l10n_loader
        )
    
    bot = Bot(
            token=settings.bot_token.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    
    dp = Dispatcher()
    
    router = setup_routers()
    
    dp.include_router(router)
    
    dp.update.middleware(L10nMiddleware(l10n))

    await set_bot_commands(bot, l10n)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    
if __name__ == "__main__":
    asyncio.run(main())