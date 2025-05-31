import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.connection import Database
from bot.utils.redis_manager import RedisManager
from bot.config import config

async def tap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Get user's current energy
    energy = await RedisManager.get_user_energy(user.id)
    if energy is None:
        energy = config.max_energy
        await RedisManager.set_user_energy(user.id, energy)
    
    # Check if user has energy
    if energy <= 0:
        await update.message.reply_text(
            "⚠️ You're out of energy! Wait for it to regenerate or buy upgrades in the shop."
        )
        return
    
    # Check rate limiting
    last_tap = await RedisManager.get_last_tap_time(user.id)
    current_time = time.time()
    if last_tap and current_time - last_tap < config.tap_cooldown:
        await update.message.reply_text(
            f"⏳ Please wait {config.tap_cooldown} seconds between taps."
        )
        return
    
    # Check taps per minute limit
    taps_this_minute = await RedisManager.increment_tap_count(user.id)
    if taps_this_minute > config.max_taps_per_minute:
        await update.message.reply_text(
            "⚠️ You're tapping too fast! Please slow down."
        )
        return
    
    # Get user's tap multiplier from upgrades
    tap_multiplier = await Database.fetchval(
        """
        SELECT COALESCE(SUM(effect_value), 1.0)
        FROM user_upgrades uu
        JOIN upgrades u ON u.id = uu.upgrade_id
        WHERE uu.user_id = $1 AND u.effect_type = 'tap_multiplier'
        """,
        user.id
    )
    
    # Calculate reward
    reward = config.base_tap_reward * tap_multiplier
    
    # Update user's balance and energy
    await Database.execute(
        """
        UPDATE users 
        SET balance = balance + $1
        WHERE user_id = $2
        """,
        reward, user.id
    )
    
    # Decrease energy
    new_energy = energy - 1
    await RedisManager.set_user_energy(user.id, new_energy)
    
    # Update last tap time
    await RedisManager.set_last_tap_time(user.id, current_time)
    
    # Log tap for analytics
    await Database.execute(
        """
        INSERT INTO taps (user_id, amount)
        VALUES ($1, $2)
        """,
        user.id, reward
    )
    
    # Update leaderboard
    await RedisManager.update_leaderboard(user.id, reward)
    
    # Create response message
    keyboard = [
        [
            InlineKeyboardButton("🎯 Tap Again", callback_data="tap"),
            InlineKeyboardButton("🏪 Shop", callback_data="shop")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"💰 +{reward:.2f} AUG\n"
        f"⚡ Energy: {new_energy}/{config.max_energy}\n\n"
        "Keep tapping to earn more!"
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def tap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tap button callback"""
    query = update.callback_query
    await query.answer()
    
    # Reuse tap logic
    update.effective_message = query.message
    await tap_command(update, context) 