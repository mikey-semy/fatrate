from aiogram import Router


def setup_routers() -> Router:
    from . import common
    from . import fat_commands
    
    router = Router()
    router.include_router(common.router)
    router.include_router(fat_commands.router)
    
    return router