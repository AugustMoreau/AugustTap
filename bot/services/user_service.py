from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from ..db.connection import Database
from ..utils.redis_manager import RedisManager
from ..config import config

class UserService:
    @staticmethod
    async def get_or_create_user(user_id: int, username: Optional[str] = None) -> dict:
        user = await Database.fetchrow(
            """
            INSERT INTO users (user_id, username)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
            SET username = COALESCE($2, users.username)
            RETURNING *
            """,
            user_id, username
        )
        return dict(user)

    @staticmethod
    async def get_user(user_id: int) -> Optional[dict]:
        user = await Database.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )
        return dict(user) if user else None

    @staticmethod
    async def get_referrals(user_id: int) -> List[Dict]:
        """Get all users referred by this user"""
        referrals = await Database.fetch(
            """
            SELECT user_id, username, balance, created_at
            FROM users
            WHERE invited_by = $1
            ORDER BY created_at DESC
            """,
            user_id
        )
        return [dict(ref) for ref in referrals]

    @staticmethod
    async def get_referral_stats(user_id: int) -> Dict:
        """Get detailed referral statistics"""
        stats = await Database.fetchrow(
            """
            SELECT 
                COUNT(*) as total_referrals,
                SUM(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END) as new_referrals_24h,
                SUM(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END) as new_referrals_7d
            FROM users
            WHERE invited_by = $1
            """,
            user_id
        )
        return dict(stats) if stats else {
            'total_referrals': 0,
            'new_referrals_24h': 0,
            'new_referrals_7d': 0
        }

    @staticmethod
    async def get_referral_earnings(user_id: int) -> Dict:
        """Get total earnings from referrals"""
        earnings = await Database.fetchrow(
            """
            SELECT 
                SUM(reward_amount) as total_earnings,
                COUNT(*) as total_rewards
            FROM referral_rewards
            WHERE referrer_id = $1
            """,
            user_id
        )
        return dict(earnings) if earnings else {
            'total_earnings': 0,
            'total_rewards': 0
        }

    @staticmethod
    async def update_energy(user_id: int, energy: int) -> None:
        await Database.execute(
            "UPDATE users SET energy = $1 WHERE user_id = $2",
            energy, user_id
        )

    @staticmethod
    async def update_balance(user_id: int, amount: int) -> None:
        await Database.execute(
            "UPDATE users SET balance = balance + $1 WHERE user_id = $2",
            amount, user_id
        )

    @staticmethod
    async def get_energy_info(user_id: int) -> Tuple[int, datetime]:
        user = await Database.fetchrow(
            "SELECT energy, last_tap_time FROM users WHERE user_id = $1",
            user_id
        )
        if not user:
            return 0, datetime.now()

        last_tap = user['last_tap_time'] or datetime.now()
        current_energy = user['energy']

        # Calculate regenerated energy
        time_diff = datetime.now() - last_tap
        regen_minutes = int(time_diff.total_seconds() / 60)
        regen_energy = min(
            regen_minutes // config.game.energy_regen_minutes,
            config.game.max_energy - current_energy
        )

        if regen_energy > 0:
            current_energy = min(current_energy + regen_energy, config.game.max_energy)
            await UserService.update_energy(user_id, current_energy)

        return current_energy, last_tap

    @staticmethod
    async def can_tap(user_id: int) -> bool:
        energy, _ = await UserService.get_energy_info(user_id)
        return energy > 0

    @staticmethod
    async def process_tap(user_id: int) -> Tuple[int, int]:
        """Process a tap and return (reward, remaining_energy)"""
        if not await UserService.can_tap(user_id):
            return 0, 0

        # Get user's tap power upgrade
        tap_power = await Database.fetchval(
            """
            SELECT level FROM user_upgrades 
            WHERE user_id = $1 AND upgrade_type = 'tap_power'
            """,
            user_id
        ) or 0

        # Calculate reward
        base_reward = config.game.base_tap_reward
        bonus = min(tap_power, config.game.max_bonus_reward)
        total_reward = base_reward + bonus

        # Start transaction
        async with Database.get_pool().acquire() as conn:
            async with conn.transaction():
                # Update user state
                await conn.execute(
                    """
                    UPDATE users 
                    SET energy = energy - 1,
                        balance = balance + $1,
                        last_tap_time = CURRENT_TIMESTAMP
                    WHERE user_id = $2
                    """,
                    total_reward, user_id
                )

                # Process referral bonus if applicable
                user_data = await conn.fetchrow(
                    "SELECT invited_by FROM users WHERE user_id = $1",
                    user_id
                )
                
                if user_data and user_data['invited_by']:
                    referrer_id = user_data['invited_by']
                    bonus_percent = await UserService.get_referral_bonus(user_id, referrer_id)
                    
                    if bonus_percent > 0:
                        referral_reward = int(total_reward * (bonus_percent / 100))
                        
                        # Update referrer's balance
                        await conn.execute(
                            """
                            UPDATE users 
                            SET balance = balance + $1
                            WHERE user_id = $2
                            """,
                            referral_reward, referrer_id
                        )
                        
                        # Record referral reward
                        await conn.execute(
                            """
                            INSERT INTO referral_rewards 
                            (referrer_id, referred_id, reward_amount, tap_reward)
                            VALUES ($1, $2, $3, $4)
                            """,
                            referrer_id, user_id, referral_reward, total_reward
                        )

        # Get remaining energy
        energy, _ = await UserService.get_energy_info(user_id)

        return total_reward, energy

    @staticmethod
    async def process_referral(inviter_id: int, new_user_id: int) -> None:
        """Process a new referral"""
        await Database.execute(
            """
            UPDATE users 
            SET referrals = referrals + 1
            WHERE user_id = $1
            """,
            inviter_id
        )

        await Database.execute(
            """
            UPDATE users 
            SET invited_by = $1
            WHERE user_id = $2
            """,
            inviter_id, new_user_id
        )

    @staticmethod
    async def get_referral_bonus(user_id: int, referrer_id: int) -> int:
        """Calculate referral bonus for a tap"""
        tap_count = await Database.fetchval(
            """
            SELECT tap_count FROM referral_taps
            WHERE user_id = $1 AND referrer_id = $2
            """,
            user_id, referrer_id
        ) or 0

        if tap_count >= config.game.referral_bonus_taps:
            return 0

        await Database.execute(
            """
            UPDATE referral_taps
            SET tap_count = tap_count + 1
            WHERE user_id = $1 AND referrer_id = $2
            """,
            user_id, referrer_id
        )

        return config.game.referral_bonus_percent 