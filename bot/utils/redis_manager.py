import aioredis
from bot.config import config

class RedisManager:
    _redis = None

    @classmethod
    async def get_redis(cls):
        if cls._redis is None:
            cls._redis = await aioredis.from_url(
                config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._redis

    @classmethod
    async def close(cls):
        if cls._redis:
            await cls._redis.close()
            cls._redis = None

    @classmethod
    async def get_user_energy(cls, user_id: int) -> int:
        redis = await cls.get_redis()
        key = f"energy:{user_id}"
        energy = await redis.get(key)
        return int(energy) if energy else None

    @classmethod
    async def set_user_energy(cls, user_id: int, energy: int, expire: int = None):
        redis = await cls.get_redis()
        key = f"energy:{user_id}"
        if expire:
            await redis.set(key, energy, ex=expire)
        else:
            await redis.set(key, energy)

    @classmethod
    async def get_last_tap_time(cls, user_id: int) -> float:
        redis = await cls.get_redis()
        key = f"last_tap:{user_id}"
        timestamp = await redis.get(key)
        return float(timestamp) if timestamp else None

    @classmethod
    async def set_last_tap_time(cls, user_id: int, timestamp: float):
        redis = await cls.get_redis()
        key = f"last_tap:{user_id}"
        await redis.set(key, timestamp)

    @classmethod
    async def get_last_daily_claim(cls, user_id: int) -> float:
        redis = await cls.get_redis()
        key = f"daily_claim:{user_id}"
        timestamp = await redis.get(key)
        return float(timestamp) if timestamp else None

    @classmethod
    async def set_last_daily_claim(cls, user_id: int, timestamp: float):
        redis = await cls.get_redis()
        key = f"daily_claim:{user_id}"
        await redis.set(key, timestamp)

    @classmethod
    async def increment_tap_count(cls, user_id: int, window: int = 60) -> int:
        redis = await cls.get_redis()
        key = f"tap_count:{user_id}"
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        return results[0]

    @classmethod
    async def get_leaderboard(cls) -> list:
        redis = await cls.get_redis()
        key = "leaderboard"
        return await redis.zrevrange(key, 0, 9, withscores=True)

    @classmethod
    async def update_leaderboard(cls, user_id: int, score: float):
        redis = await cls.get_redis()
        key = "leaderboard"
        await redis.zadd(key, {str(user_id): score}) 