import asyncio
import logging
import signal
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config.settings import BOT_TOKEN, UserRole
from database.manager import db_manager
from handlers import (
    admin, user, products, admin_orders, 
    payments, admin_modes, admin_stats, 
    admin_broadcast, admin_coupons, admin_audit, language
)
from middlewares.auth import AuthMiddleware, AdminMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.error_handler import ErrorHandlerMiddleware

# إعداد الـ Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def shutdown(bot: Bot, dp: Dispatcher):
    """إيقاف البوت بشكل آمن"""
    logger.info("Shutting down...")
    await dp.stop_polling()
    await bot.session.close()
    logger.info("Bot stopped successfully!")

async def main():
    """الدالة الرئيسية لتشغيل البوت v2.3 REBORN"""
    logger.info("Starting Story Bot v2.3 REBORN...")
    
    # تهيئة قاعدة البيانات
    await db_manager.init_db()
    
    # إنشاء Bot و Dispatcher
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
    dp = Dispatcher(storage=MemoryStorage())
    
    # تسجيل الميدلوير بالترتيب الصحيح (v2.3 REBORN)
    # الترتيب: ErrorHandler -> Throttling -> Admin -> Auth
    
    # للرسائل
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(AdminMiddleware())
    dp.message.middleware(AuthMiddleware())
    
    # للـ Callback Queries (الأزرار)
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # تسجيل الموجهات (Routers) بالترتيب الصحيح
    # الأدمن أولاً لضمان الأولوية
    dp.include_router(admin.router)
    dp.include_router(admin_orders.router)
    dp.include_router(products.router)
    dp.include_router(payments.router)
    dp.include_router(admin_modes.router)
    dp.include_router(admin_stats.router)
    dp.include_router(admin_broadcast.router)
    dp.include_router(admin_coupons.router)
    dp.include_router(admin_audit.router)
    dp.include_router(language.router)
    
    # اليوزر آخراً كـ Fallback
    dp.include_router(user.router)
    
    # حذف الـ Webhook القديم وبدء الـ Polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown(bot, dp)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
