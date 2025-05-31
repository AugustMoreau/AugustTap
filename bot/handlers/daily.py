import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.connection import Database
from bot.utils.redis_manager import RedisManager
from bot.config import config

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Get user's last daily claim
    last_claim = await RedisManager.get_last_daily_claim(user.id)
    current_time = time.time()
    
    if last_claim:
        time_since_last_claim = current_time - last_claim
        hours_remaining = 24 - (time_since_last_claim / 3600)
        
        if hours_remaining > 0:
            await update.message.reply_text(
                f"⏳ You can claim your daily reward in {hours_remaining:.1f} hours."
            )
            return
    
    # Process daily claim
    async with Database.get_pool().acquire() as conn:
        async with conn.transaction():
            # Add reward to user's balance
            await conn.execute(
                """
                UPDATE users 
                SET balance = balance + $1
                WHERE user_id = $2
                """,
                config.daily_reward, user.id
            )
            
            # Log daily claim
            await conn.execute(
                """
                INSERT INTO daily_claims (user_id, amount)
                VALUES ($1, $2)
                """,
                user.id, config.daily_reward
            )
    
    # Update last claim time
    await RedisManager.set_last_daily_claim(user.id, current_time)
    
    # Create success message
    keyboard = [
        [
            InlineKeyboardButton("🎯 Tap", callback_data="tap"),
            InlineKeyboardButton("👤 Profile", callback_data="profile")
        ],
        [
            InlineKeyboardButton("🏪 Shop", callback_data="shop"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"🎁 Daily Reward Claimed!\n\n"
        f"💰 +{config.daily_reward:.2f} AUG added to your balance.\n\n"
        "Come back tomorrow for another reward!"
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup) 