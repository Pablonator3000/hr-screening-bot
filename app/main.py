import logging
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from app.config import settings
from app.bot.handlers import screening, admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.tg_bot_token)
dp = Dispatcher(storage=MemoryStorage())


polling_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task

    if not dp.sub_routers:
        logger.info("Including routers...")
        dp.include_router(admin.router)
        dp.include_router(screening.router)

    # старт
    try:
        if settings.webhook_url:
            webhook_url = settings.webhook_url

            info = await bot.get_webhook_info()
            if info.url != webhook_url:
                # drop_pending_updates=True обычно удобно при деплое,
                # чтобы не ловить очередь старых апдейтов.
                await bot.set_webhook(url=webhook_url, drop_pending_updates=True)

            logger.info("Webhook mode. Webhook set to %s", webhook_url)
        else:
            # polling режим: обязательно удалить вебхук, если он был установлен ранее
            await bot.delete_webhook(drop_pending_updates=True)

            polling_task = asyncio.create_task(dp.start_polling(bot))
            logger.warning("Polling mode. webhook_url not set; started polling task.")
    except Exception as e:
        logger.error(f"Error during bot startup: {e}", exc_info=True)

    yield

    # shutdown
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    await bot.session.close()
    logger.info("Bot session closed.")


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def telegram_webhook(request: Request, background: BackgroundTasks):
    """
    Telegram ждёт быстрый 200 OK.
    Поэтому распарсили апдейт и отправили обработку в background.
    """
    data = await request.json()
    update = types.Update.model_validate(data, context={"bot": bot})
    background.add_task(dp.feed_update, bot, update)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000
    )