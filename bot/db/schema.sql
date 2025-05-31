-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    balance BIGINT DEFAULT 0,
    energy INTEGER DEFAULT 100,
    last_tap_time TIMESTAMP WITH TIME ZONE,
    referrals INTEGER DEFAULT 0,
    invited_by BIGINT REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User upgrades table
CREATE TABLE IF NOT EXISTS user_upgrades (
    user_id BIGINT REFERENCES users(user_id),
    upgrade_type VARCHAR(50),
    level INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, upgrade_type)
);

-- Daily claims table
CREATE TABLE IF NOT EXISTS daily_claims (
    user_id BIGINT REFERENCES users(user_id),
    claimed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, DATE(claimed_at))
);

-- Referral tracking table
CREATE TABLE IF NOT EXISTS referral_taps (
    user_id BIGINT REFERENCES users(user_id),
    referrer_id BIGINT REFERENCES users(user_id),
    tap_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, referrer_id)
);

-- Referral rewards table
CREATE TABLE IF NOT EXISTS referral_rewards (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT REFERENCES users(user_id),
    referred_id BIGINT REFERENCES users(user_id),
    reward_amount BIGINT NOT NULL,
    tap_reward BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance DESC);
CREATE INDEX IF NOT EXISTS idx_users_referrals ON users(referrals DESC);
CREATE INDEX IF NOT EXISTS idx_daily_claims_date ON daily_claims(DATE(claimed_at));
CREATE INDEX IF NOT EXISTS idx_referral_rewards_referrer ON referral_rewards(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_rewards_referred ON referral_rewards(referred_id); 