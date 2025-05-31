-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    balance DECIMAL(20, 8) DEFAULT 0,
    energy INTEGER DEFAULT 100,
    max_energy INTEGER DEFAULT 100,
    last_tap_time TIMESTAMP,
    last_daily_claim TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create upgrades table
CREATE TABLE IF NOT EXISTS upgrades (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_cost DECIMAL(20, 8) NOT NULL,
    cost_multiplier DECIMAL(10, 2) DEFAULT 1.1,
    effect_type VARCHAR(50) NOT NULL,
    effect_value DECIMAL(20, 8) NOT NULL,
    max_level INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_upgrades table
CREATE TABLE IF NOT EXISTS user_upgrades (
    user_id BIGINT REFERENCES users(user_id),
    upgrade_id INTEGER REFERENCES upgrades(id),
    level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, upgrade_id)
);

-- Create referrals table
CREATE TABLE IF NOT EXISTS referrals (
    referrer_id BIGINT REFERENCES users(user_id),
    referred_id BIGINT REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (referrer_id, referred_id)
);

-- Create taps table for analytics
CREATE TABLE IF NOT EXISTS taps (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    amount DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create daily_claims table
CREATE TABLE IF NOT EXISTS daily_claims (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    amount DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial upgrades
INSERT INTO upgrades (name, description, base_cost, effect_type, effect_value) VALUES
    ('Tap Power', 'Increases the amount earned per tap', 10, 'tap_multiplier', 1.1),
    ('Energy Capacity', 'Increases maximum energy', 50, 'max_energy', 10),
    ('Energy Regen', 'Increases energy regeneration rate', 100, 'energy_regen', 1),
    ('Referral Bonus', 'Increases earnings from referrals', 200, 'referral_bonus', 0.1);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_taps_user_id ON taps(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_claims_user_id ON daily_claims(user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id); 