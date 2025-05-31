import asyncio
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler
)
from bot.config import config
from bot.db.connection import Database
from bot.utils.redis_manager import RedisManager

# Import handlers
from bot.handlers.start import start_command
from bot.handlers.tap import tap_command, tap_callback
from bot.handlers.profile import profile_command
from bot.handlers.shop import shop_command, shop_callback
from bot.handlers.leaderboard import leaderboard_command, leaderboard_callback
from bot.handlers.invite import invite_command, invite_callback, back_to_invite_callback
from bot.handlers.daily import daily_command

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    # Initialize database
    await Database.get_pool()
    
    # Initialize Redis
    await RedisManager.get_redis()
    
    # Create bot application
    application = ApplicationBuilder().token(config.bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("tap", tap_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("shop", shop_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("invite", invite_command))
    application.add_handler(CommandHandler("daily", daily_command))
    
    # Add callback handlers
    application.add_handler(CallbackQueryHandler(tap_callback, pattern="^tap$"))
    application.add_handler(CallbackQueryHandler(shop_callback, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^lb_"))
    application.add_handler(CallbackQueryHandler(invite_callback, pattern="^view_referrals$"))
    application.add_handler(CallbackQueryHandler(back_to_invite_callback, pattern="^back_to_invite$"))
    
    # Start the bot
    await application.initialize()
    await application.start()
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}")
    finally:
        # Cleanup
        asyncio.run(Database.close())
        asyncio.run(RedisManager.close()) 