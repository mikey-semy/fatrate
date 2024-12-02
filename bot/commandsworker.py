from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault
from fluent.runtime import FluentLocalization

async def set_bot_commands(bot: Bot, l10n: FluentLocalization):
    commands = [
        BotCommand(command="start", description=l10n.format_value("intro-description")),
        BotCommand(command="help", description=l10n.format_value("help-description")),
        BotCommand(command="add", description=l10n.format_value("add-description")),
        BotCommand(command="update", description=l10n.format_value("update-description")),
        BotCommand(command="rating", description=l10n.format_value("rating-description")),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())