# Augustus Tap - Telegram Tap-to-Earn Bot

A Telegram bot that allows users to earn AUG tokens by tapping, completing daily tasks, and inviting friends.

## Features

- 🎯 Tap to earn AUG tokens
- ⚡ Energy system with regeneration
- 🏪 Shop with upgrades
- 👥 Referral system with bonuses
- 🎁 Daily rewards
- 🏆 Leaderboards
- 💰 Upgrade system with multipliers

## Tech Stack

- Python 3.10+
- python-telegram-bot v20.x (async)
- PostgreSQL for persistent data
- Redis for caching and rate limiting
- Docker for deployment

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/augustus-tap.git
cd augustus-tap
```

2. Create a `.env` file:
```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/augustus_tap
REDIS_URL=redis://localhost:6379/0
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
psql -U postgres -d augustus_tap -f migrations/001_initial_schema.sql
```

5. Start the bot:
```bash
python -m bot.main
```

## Docker Setup

1. Build and start containers:
```bash
docker-compose up -d
```

2. Run migrations:
```bash
docker-compose exec bot psql -U postgres -d augustus_tap -f /app/migrations/001_initial_schema.sql
```

## Commands

- `/start` - Start the bot and get your referral link
- `/tap` - Tap to earn AUG tokens
- `/profile` - View your stats and upgrades
- `/shop` - Buy upgrades
- `/leaderboard` - View top players
- `/invite` - Get your referral link
- `/daily` - Claim daily reward

## Game Mechanics

### Tapping
- Each tap costs 1 energy
- Base reward: 1 AUG per tap
- Energy regenerates over time
- Upgrades increase tap rewards

### Upgrades
- Tap Power: Increases tap rewards
- Energy Capacity: Increases max energy
- Energy Regen: Increases regeneration rate
- Referral Bonus: Increases referral earnings

### Referrals
- Get 10 AUG for each friend who joins
- Track your referral earnings
- Compete on the referral leaderboard

### Daily Rewards
- Claim 50 AUG every 24 hours
- Rewards increase with upgrades

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 