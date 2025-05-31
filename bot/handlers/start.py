from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.connection import Database
from bot.utils.redis_manager import RedisManager
from bot.config import config

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    
    # Check if user exists
    user_data = await Database.fetchrow(
        "SELECT * FROM users WHERE user_id = $1",
        user.id
    )
    
    if not user_data:
        # Register new user
        await Database.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES ($1, $2, $3, $4)
            """,
            user.id, user.username, user.first_name, user.last_name
        )
        
        # Set initial energy in Redis
        await RedisManager.set_user_energy(user.id, config.max_energy)
        
        # Handle referral if present
        if args and args[0].startswith('ref_'):
            try:
                referrer_id = int(args[0][4:])
                if referrer_id != user.id:  # Prevent self-referral
                    await Database.execute(
                        """
                        INSERT INTO referrals (referrer_id, referred_id)
                        VALUES ($1, $2)
                        """,
                        referrer_id, user.id
                    )
                    # Add referral bonus to referrer
                    await Database.execute(
                        """
                        UPDATE users 
                        SET balance = balance + $1
                        WHERE user_id = $2
                        """,
                        config.referral_bonus, referrer_id
                    )
            except (ValueError, IndexError):
                pass  # Invalid referral code, ignore
    
    # Create welcome message with inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("🎯 Tap", callback_data="tap"),
            InlineKeyboardButton("👤 Profile", callback_data="profile")
        ],
        [
            InlineKeyboardButton("🏪 Shop", callback_data="shop"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton("🎁 Daily Reward", callback_data="daily"),
            InlineKeyboardButton("👥 Invite Friends", callback_data="invite")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 Welcome to Augustus Tap, {user.first_name}!\n\n"
        "🎮 Earn AUG tokens by tapping and completing daily tasks.\n"
        "💪 Use your energy wisely and upgrade your tapping power.\n"
        "👥 Invite friends to earn referral bonuses!\n\n"
        "What would you like to do?"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup) 