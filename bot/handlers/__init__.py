from aiogram import Router


def setup_routers() -> Router:
    from . import common
    
    router = Router()
    router.include_router(common.router)
    
    return router