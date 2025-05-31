from typing import List, Dict
from ..db.connection import Database
from ..utils.redis_manager import RedisManager

class LeaderboardService:
    CACHE_TTL = 300  # 5 minutes

    @staticmethod
    async def get_top_users(limit: int = 10) -> List[Dict]:
        # Try to get from cache first
        cache_key = f"leaderboard:top_users:{limit}"
        cached = await RedisManager.get(cache_key)
        if cached:
            return eval(cached)  # Safe as we control the data

        # Get from database
        users = await Database.fetch(
            """
            SELECT user_id, username, balance, referrals
            FROM users
            ORDER BY balance DESC
            LIMIT $1
            """,
            limit
        )

        result = [dict(user) for user in users]
        
        # Cache the result
        await RedisManager.set(cache_key, str(result), LeaderboardService.CACHE_TTL)
        
        return result

    @staticmethod
    async def get_top_referrers(limit: int = 10) -> List[Dict]:
        # Try to get from cache first
        cache_key = f"leaderboard:top_referrers:{limit}"
        cached = await RedisManager.get(cache_key)
        if cached:
            return eval(cached)  # Safe as we control the data

        # Get from database
        users = await Database.fetch(
            """
            SELECT user_id, username, referrals
            FROM users
            WHERE referrals > 0
            ORDER BY referrals DESC
            LIMIT $1
            """,
            limit
        )

        result = [dict(user) for user in users]
        
        # Cache the result
        await RedisManager.set(cache_key, str(result), LeaderboardService.CACHE_TTL)
        
        return result

    @staticmethod
    async def get_user_rank(user_id: int) -> int:
        rank = await Database.fetchval(
            """
            SELECT COUNT(*) + 1
            FROM users
            WHERE balance > (
                SELECT balance
                FROM users
                WHERE user_id = $1
            )
            """,
            user_id
        )
        return rank or 0

    @staticmethod
    async def get_user_referral_rank(user_id: int) -> int:
        rank = await Database.fetchval(
            """
            SELECT COUNT(*) + 1
            FROM users
            WHERE referrals > (
                SELECT referrals
                FROM users
                WHERE user_id = $1
            )
            """,
            user_id
        )
        return rank or 0

    @staticmethod
    async def invalidate_cache():
        """Invalidate all leaderboard caches"""
        keys = await RedisManager.get_redis().keys("leaderboard:*")
        if keys:
            await RedisManager.get_redis().delete(*keys) 