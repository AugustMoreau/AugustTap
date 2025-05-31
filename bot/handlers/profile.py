from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.connection import Database
from bot.utils.redis_manager import RedisManager
from bot.config import config

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Get user data
    user_data = await Database.fetchrow(
        """
        SELECT u.*, 
               COUNT(DISTINCT r.referred_id) as referral_count,
               COALESCE(SUM(t.amount), 0) as total_earned
        FROM users u
        LEFT JOIN referrals r ON r.referrer_id = u.user_id
        LEFT JOIN taps t ON t.user_id = u.user_id
        WHERE u.user_id = $1
        GROUP BY u.user_id
        """,
        user.id
    )
    
    if not user_data:
        await update.message.reply_text(
            "⚠️ You haven't started playing yet! Use /start to begin."
        )
        return
    
    # Get user's energy
    energy = await RedisManager.get_user_energy(user.id)
    if energy is None:
        energy = config.max_energy
        await RedisManager.set_user_energy(user.id, energy)
    
    # Get user's upgrades
    upgrades = await Database.fetch(
        """
        SELECT u.name, uu.level, u.effect_type, u.effect_value
        FROM user_upgrades uu
        JOIN upgrades u ON u.id = uu.upgrade_id
        WHERE uu.user_id = $1
        ORDER BY u.id
        """,
        user.id
    )
    
    # Create profile message
    profile_text = (
        f"👤 Profile: {user.first_name}\n\n"
        f"💰 Balance: {user_data['balance']:.2f} AUG\n"
        f"⚡ Energy: {energy}/{config.max_energy}\n"
        f"👥 Referrals: {user_data['referral_count']}\n"
        f"💎 Total Earned: {user_data['total_earned']:.2f} AUG\n\n"
    )
    
    if upgrades:
        profile_text += "🔧 Upgrades:\n"
        for upgrade in upgrades:
            effect = f"+{upgrade['effect_value'] * upgrade['level']:.1f}"
            if upgrade['effect_type'] == 'tap_multiplier':
                effect += "x"
            profile_text += f"• {upgrade['name']} (Lvl {upgrade['level']}): {effect}\n"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("🎯 Tap", callback_data="tap"),
            InlineKeyboardButton("🏪 Shop", callback_data="shop")
        ],
        [
            InlineKeyboardButton("👥 Invite Friends", callback_data="invite"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(profile_text, reply_markup=reply_markup) 