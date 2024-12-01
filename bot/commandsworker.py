from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault
from fluent.runtime import FluentLocalization

async def set_bot_commands(bot: Bot, l10n: FluentLocalization):
    commands = [
        BotCommand(command="start", description=l10n.format_value("start_description")),
        BotCommand(command="help", description=l10n.format_value("help_description")),
        BotCommand(command="add_fat", description=l10n.format_value("add_fat_description")),
        BotCommand(command="update_fat", description=l10n.format_value("update_fat_description")),
        BotCommand(command="show_rate", description=l10n.format_value("show_rating_description")),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())