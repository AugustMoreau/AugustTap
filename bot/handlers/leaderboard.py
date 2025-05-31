from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.connection import Database
from bot.utils.redis_manager import RedisManager

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Get top players by balance
    top_balance = await Database.fetch(
        """
        SELECT u.user_id, u.username, u.first_name, u.balance
        FROM users u
        ORDER BY u.balance DESC
        LIMIT 10
        """
    )
    
    # Get top players by referrals
    top_referrals = await Database.fetch(
        """
        SELECT u.user_id, u.username, u.first_name, COUNT(r.referred_id) as referral_count
        FROM users u
        LEFT JOIN referrals r ON r.referrer_id = u.user_id
        GROUP BY u.user_id
        ORDER BY referral_count DESC
        LIMIT 10
        """
    )
    
    # Create leaderboard message
    leaderboard_text = "🏆 Leaderboard\n\n"
    
    # Balance rankings
    leaderboard_text += "💰 Top Players by Balance:\n"
    for i, player in enumerate(top_balance, 1):
        name = player['username'] or player['first_name']
        leaderboard_text += f"{i}. {name}: {player['balance']:.2f} AUG\n"
    
    leaderboard_text += "\n👥 Top Players by Referrals:\n"
    for i, player in enumerate(top_referrals, 1):
        name = player['username'] or player['first_name']
        leaderboard_text += f"{i}. {name}: {player['referral_count']} referrals\n"
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("🎯 Tap", callback_data="tap"),
            InlineKeyboardButton("👤 Profile", callback_data="profile")
        ],
        [
            InlineKeyboardButton("🏪 Shop", callback_data="shop"),
            InlineKeyboardButton("👥 Invite Friends", callback_data="invite")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(leaderboard_text, reply_markup=reply_markup)

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard button callback"""
    query = update.callback_query
    await query.answer()
    
    # Reuse leaderboard logic
    update.effective_message = query.message
    await leaderboard_command(update, context) 