from dataclasses import dataclass, field
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "augustus_tap")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")

@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))

@dataclass
class GameConfig:
    max_energy: int = int(os.getenv("MAX_ENERGY", "100"))
    energy_regen_minutes: int = int(os.getenv("ENERGY_REGEN_MINUTES", "5"))
    base_tap_reward: int = int(os.getenv("BASE_TAP_REWARD", "1"))
    max_bonus_reward: int = int(os.getenv("MAX_BONUS_REWARD", "5"))
    referral_bonus_percent: int = int(os.getenv("REFERRAL_BONUS_PERCENT", "20"))
    referral_bonus_taps: int = int(os.getenv("REFERRAL_BONUS_TAPS", "100"))
    tax_percent: int = int(os.getenv("TAX_PERCENT", "10"))
    max_supply: int = int(os.getenv("MAX_SUPPLY", "1000000000"))

class Config:
    # Bot configuration
    bot_token = os.getenv("BOT_TOKEN")
    
    # Database configuration
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/augustus_tap")
    
    # Redis configuration
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Game configuration
    base_tap_reward = float(os.getenv("BASE_TAP_REWARD", "1.0"))
    energy_regen_rate = int(os.getenv("ENERGY_REGEN_RATE", "1"))  # energy points per minute
    max_energy = int(os.getenv("MAX_ENERGY", "100"))
    daily_reward = float(os.getenv("DAILY_REWARD", "50.0"))
    referral_bonus = float(os.getenv("REFERRAL_BONUS", "10.0"))
    
    # Rate limiting
    tap_cooldown = int(os.getenv("TAP_COOLDOWN", "1"))  # seconds
    max_taps_per_minute = int(os.getenv("MAX_TAPS_PER_MINUTE", "60"))
    
    # Tax configuration
    shop_tax_rate = float(os.getenv("SHOP_TAX_RATE", "0.1"))  # 10% tax on shop purchases

    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    game: GameConfig = field(default_factory=GameConfig)

config = Config() 