from aiogram import Router, types
from aiogram.filters import Command
from fluent.runtime import FluentLocalization
from bot.database.database import Database
from bot.handlers.prefix import get_fat_prefix
from logging import info, error

router = Router()


@router.message(Command("add"))
async def add_measurement(message: types.Message, l10n: FluentLocalization, db: Database):
    
    args = message.text.split()
        
    if len(args) != 3:
        error(l10n.format_value("error-add"))
        await message.reply(l10n.format_value("add-error"))
        return
    
    try:
        height = float(args[1])
        weight = float(args[2])
        
        if not(30 <= weight <= 200) or not(100 <= height <= 250):
            raise ValueError
        
        info(f"Пользователь {message.from_user.username} прошел проверку на значения: {not(30 <= weight <= 200) or not(100 <= height <= 250)}")
        
        db.add_measurement(
            user_id=message.from_user.id, 
            username=message.from_user.username, 
            height=height,
            weight=weight,
            chat_id=message.chat.id
            )
        info(f"Пользователь {message.from_user.username} добавил данные в базу данных")
        await message.answer(l10n.format_value("add-success", {
                                    "height": height,
                                    "weight": weight
                            }))
            
    except (IndexError, ValueError):
        error(l10n.format_value("error-add"))
        await message.reply(l10n.format_value("add-error"))

@router.message(Command("update"))
async def update_measurement(message: types.Message, l10n: FluentLocalization, db: Database):
    try:
        weight = float(message.text.split()[1])
        if not (30 <= weight <= 300):
            raise ValueError
        
        user = db.get_user(message.from_user.id, message.chat.id)
        if not user:
            error(l10n.format_value("error-user-not-found"))
            await message.reply(l10n.format_value("no-user-error"))
            return
        
        db.update_weight(message.from_user.id, weight, message.chat.id)
        info(l10n.format_value("info-update-success"))
        await message.answer(l10n.format_value("update-success", {"weight": weight}))
    except (IndexError, ValueError):
        error(l10n.format_value("error-update"))
        await message.reply(l10n.format_value("update-error"))

@router.message(Command("rating"))
async def show_stats(message: types.Message, l10n: FluentLocalization, db: Database):
    rating = db.get_stats(message.chat.id)
    if not rating:
        info(l10n.format_value("info-rating-empty"))
        await message.answer(l10n.format_value("rating-empty"))
        return
    
    response = l10n.format_value("rating-header") + "\n\n"
    
    for i, (user_id,username, weight, bmi, date) in enumerate(rating, start=1):
        
        user = username or "Анонимус"
        
        curr_prefix = db.get_prefix(user_id, message.chat.id)
        curr_status = db.get_status(user_id, message.chat.id)
        
        response += l10n.format_value("rating-item", {
            "position": i,
            "prefix": curr_prefix ,
            "username": user,
            "weight": weight,
            "bmi": f"{bmi:.1f}",
            "status": curr_status,
            "date": date,
        }) + "\n"
        
        
    await message.answer(response)
    info(l10n.format_value("info-rating-showen"))
