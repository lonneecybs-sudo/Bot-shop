#!/usr/bin/env python3
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, ADMIN_ID

# Импортируем роутеры
from handlers.start import router as start_router
from handlers.order import router as order_router
from handlers.payment import router as payment_router
from handlers.admin import router as admin_router
from handlers.reviews import router as reviews_router

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем все роутеры
    dp.include_router(start_router)
    dp.include_router(order_router)
    dp.include_router(payment_router)
    dp.include_router(admin_router)
    dp.include_router(reviews_router)
    
    logger.info("=" * 50)
    logger.info("🚀 БОТ ЗАПУЩЕН!")
    logger.info("=" * 50)
    logger.info(f"👤 Админ ID: {ADMIN_ID}")
    logger.info("=" * 50)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
