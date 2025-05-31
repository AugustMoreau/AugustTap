from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.connection import Database
from bot.config import config

async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Get user's referral stats
    referral_stats = await Database.fetchrow(
        """
        SELECT 
            COUNT(DISTINCT r.referred_id) as total_referrals,
            COALESCE(SUM(u.balance), 0) as total_earned
        FROM users u
        LEFT JOIN referrals r ON r.referrer_id = u.user_id
        WHERE u.user_id = $1
        GROUP BY u.user_id
        """,
        user.id
    )
    
    if not referral_stats:
        await update.message.reply_text(
            "⚠️ You haven't started playing yet! Use /start to begin."
        )
        return
    
    # Generate referral link
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user.id}"
    
    # Create invite message
    invite_text = (
        f"👥 Invite Friends\n\n"
        f"📊 Your Referral Stats:\n"
        f"• Total Referrals: {referral_stats['total_referrals']}\n"
        f"• Total Earned: {referral_stats['total_earned']:.2f} AUG\n\n"
        f"🎁 Referral Bonus: {config.referral_bonus} AUG per friend\n\n"
        f"🔗 Your Referral Link:\n"
        f"{referral_link}\n\n"
        "Share this link with your friends to earn bonuses when they join!"
    )
    
    # Create keyboard
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
    
    await update.message.reply_text(invite_text, reply_markup=reply_markup)

async def invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle invite button callback"""
    query = update.callback_query
    await query.answer()
    
    # Reuse invite logic
    update.effective_message = query.message
    await invite_command(update, context)

async def back_to_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to invite button callback"""
    query = update.callback_query
    await query.answer()
    
    # Reuse invite logic
    update.effective_message = query.message
    await invite_command(update, context) 