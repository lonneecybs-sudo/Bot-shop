#!/usr/bin/env python3
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем конфигурацию
from config import TOKEN, ADMIN_ID, logger

# Импортируем обработчики
from handlers import start, order, payment, admin, reviews

async def main():
    """Главная функция запуска бота"""
    
    # Инициализация бота и диспетчера
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем все обработчики
    start.register_handlers(dp)
    order.register_handlers(dp)
    payment.register_handlers(dp)
    admin.register_handlers(dp)
    reviews.register_handlers(dp)
    
    # Логируем запуск
    logger.info("=" * 50)
    logger.info("🚀 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
    logger.info("=" * 50)
    logger.info(f"👤 Админ ID: {ADMIN_ID}")
    logger.info(f"🤖 Имя бота: @KRIchiboBot")
    logger.info(f"📁 Папка проекта: shop")
    logger.info(f"💾 Хранилище: MemoryStorage")
    logger.info("=" * 50)
    
    # Запускаем поллинг
    try:
        await dp.start_polling(bot)
    finally:
        # Закрываем соединения при остановке
        await bot.session.close()
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
