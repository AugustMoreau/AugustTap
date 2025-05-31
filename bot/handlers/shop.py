from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.db.connection import Database
from bot.config import config

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Get user's balance
    user_data = await Database.fetchrow(
        "SELECT balance FROM users WHERE user_id = $1",
        user.id
    )
    
    if not user_data:
        await update.message.reply_text(
            "⚠️ You haven't started playing yet! Use /start to begin."
        )
        return
    
    # Get available upgrades
    upgrades = await Database.fetch(
        """
        SELECT u.*, COALESCE(uu.level, 0) as current_level
        FROM upgrades u
        LEFT JOIN user_upgrades uu ON uu.upgrade_id = u.id AND uu.user_id = $1
        ORDER BY u.id
        """,
        user.id
    )
    
    # Create shop message
    shop_text = (
        f"🏪 Shop\n\n"
        f"💰 Your Balance: {user_data['balance']:.2f} AUG\n\n"
        "Available Upgrades:\n"
    )
    
    keyboard = []
    for upgrade in upgrades:
        # Calculate cost for next level
        current_level = upgrade['current_level']
        if current_level >= upgrade['max_level']:
            cost_text = "MAX LEVEL"
            callback_data = "max_level"
        else:
            cost = upgrade['base_cost'] * (upgrade['cost_multiplier'] ** current_level)
            cost_text = f"{cost:.2f} AUG"
            callback_data = f"buy_{upgrade['id']}"
        
        # Format effect text
        effect = f"+{upgrade['effect_value']:.1f}"
        if upgrade['effect_type'] == 'tap_multiplier':
            effect += "x"
        
        shop_text += (
            f"• {upgrade['name']} (Lvl {current_level}/{upgrade['max_level']})\n"
            f"  {upgrade['description']}\n"
            f"  Effect: {effect}\n"
            f"  Cost: {cost_text}\n\n"
        )
        
        if current_level < upgrade['max_level']:
            keyboard.append([
                InlineKeyboardButton(
                    f"Buy {upgrade['name']} - {cost_text}",
                    callback_data=callback_data
                )
            ])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("🎯 Tap", callback_data="tap"),
        InlineKeyboardButton("👤 Profile", callback_data="profile")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(shop_text, reply_markup=reply_markup)

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shop purchase callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("buy_"):
        return
    
    user = query.from_user
    upgrade_id = int(query.data[4:])
    
    # Get upgrade info
    upgrade = await Database.fetchrow(
        """
        SELECT u.*, COALESCE(uu.level, 0) as current_level
        FROM upgrades u
        LEFT JOIN user_upgrades uu ON uu.upgrade_id = u.id AND uu.user_id = $1
        WHERE u.id = $2
        """,
        user.id, upgrade_id
    )
    
    if not upgrade:
        await query.edit_message_text(
            "⚠️ This upgrade is no longer available.",
            reply_markup=query.message.reply_markup
        )
        return
    
    # Check if max level
    if upgrade['current_level'] >= upgrade['max_level']:
        await query.edit_message_text(
            "⚠️ You've reached the maximum level for this upgrade!",
            reply_markup=query.message.reply_markup
        )
        return
    
    # Calculate cost
    cost = upgrade['base_cost'] * (upgrade['cost_multiplier'] ** upgrade['current_level'])
    
    # Check if user can afford it
    user_data = await Database.fetchrow(
        "SELECT balance FROM users WHERE user_id = $1",
        user.id
    )
    
    if user_data['balance'] < cost:
        await query.edit_message_text(
            "⚠️ You don't have enough AUG to buy this upgrade!",
            reply_markup=query.message.reply_markup
        )
        return
    
    # Process purchase
    async with Database.get_pool().acquire() as conn:
        async with conn.transaction():
            # Deduct cost
            await conn.execute(
                """
                UPDATE users 
                SET balance = balance - $1
                WHERE user_id = $2
                """,
                cost, user.id
            )
            
            # Add or update upgrade
            await conn.execute(
                """
                INSERT INTO user_upgrades (user_id, upgrade_id, level)
                VALUES ($1, $2, 1)
                ON CONFLICT (user_id, upgrade_id) 
                DO UPDATE SET level = user_upgrades.level + 1
                """,
                user.id, upgrade_id
            )
    
    # Show success message
    await query.edit_message_text(
        f"✅ Successfully purchased {upgrade['name']} (Level {upgrade['current_level'] + 1})!\n"
        f"💰 Spent: {cost:.2f} AUG",
        reply_markup=query.message.reply_markup
    )
    
    # Refresh shop
    await shop_command(update, context) 