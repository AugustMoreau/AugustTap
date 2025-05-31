from datetime import datetime, timedelta
from typing import Optional, Tuple
from ..db.connection import Database
from ..utils.redis_manager import RedisManager

class DailyService:
    BONUS_AMOUNT = 50  # Base daily bonus amount
    STREAK_MULTIPLIER = 0.1  # 10% increase per day in streak
    MAX_STREAK = 7  # Maximum streak days

    @staticmethod
    async def can_claim_daily(user_id: int) -> Tuple[bool, Optional[datetime]]:
        """Check if user can claim daily bonus and return last claim time if exists"""
        last_claim = await Database.fetchval(
            """
            SELECT claimed_at 
            FROM daily_claims 
            WHERE user_id = $1 
            ORDER BY claimed_at DESC 
            LIMIT 1
            """,
            user_id
        )

        if not last_claim:
            return True, None

        # Check if 24 hours have passed
        next_claim = last_claim + timedelta(days=1)
        can_claim = datetime.now() >= next_claim

        return can_claim, last_claim

    @staticmethod
    async def get_streak(user_id: int) -> int:
        """Get user's current streak"""
        claims = await Database.fetch(
            """
            SELECT claimed_at 
            FROM daily_claims 
            WHERE user_id = $1 
            ORDER BY claimed_at DESC 
            LIMIT $2
            """,
            user_id, DailyService.MAX_STREAK
        )

        if not claims:
            return 0

        streak = 1
        for i in range(len(claims) - 1):
            current = claims[i]['claimed_at']
            previous = claims[i + 1]['claimed_at']
            
            # Check if claims are on consecutive days
            if (current - previous).days == 1:
                streak += 1
            else:
                break

        return streak

    @staticmethod
    async def claim_daily(user_id: int) -> Tuple[bool, int]:
        """Claim daily bonus and return (success, amount)"""
        can_claim, _ = await DailyService.can_claim_daily(user_id)
        if not can_claim:
            return False, 0

        # Get current streak
        streak = await DailyService.get_streak(user_id)
        
        # Calculate bonus amount
        multiplier = 1 + (streak * DailyService.STREAK_MULTIPLIER)
        amount = int(DailyService.BONUS_AMOUNT * multiplier)

        # Start transaction
        async with Database.get_pool().acquire() as conn:
            async with conn.transaction():
                # Record claim
                await conn.execute(
                    """
                    INSERT INTO daily_claims (user_id)
                    VALUES ($1)
                    """,
                    user_id
                )

                # Update user balance
                await conn.execute(
                    """
                    UPDATE users 
                    SET balance = balance + $1
                    WHERE user_id = $2
                    """,
                    amount, user_id
                )

        return True, amount

    @staticmethod
    async def get_next_claim_time(user_id: int) -> Optional[datetime]:
        """Get time until next daily claim is available"""
        can_claim, last_claim = await DailyService.can_claim_daily(user_id)
        if can_claim:
            return None

        return last_claim + timedelta(days=1) 