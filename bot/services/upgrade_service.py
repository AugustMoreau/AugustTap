from typing import Optional, Dict, List
from ..db.connection import Database
from ..config import config

class UpgradeService:
    UPGRADE_TYPES = {
        'tap_power': {
            'name': 'Tap Power',
            'base_cost': 100,
            'cost_multiplier': 1.5,
            'max_level': 10
        },
        'energy_capacity': {
            'name': 'Energy Capacity',
            'base_cost': 200,
            'cost_multiplier': 2.0,
            'max_level': 5
        }
    }

    @staticmethod
    async def get_upgrade_cost(upgrade_type: str, current_level: int) -> int:
        if upgrade_type not in UpgradeService.UPGRADE_TYPES:
            return 0

        upgrade_info = UpgradeService.UPGRADE_TYPES[upgrade_type]
        base_cost = upgrade_info['base_cost']
        multiplier = upgrade_info['cost_multiplier']
        
        return int(base_cost * (multiplier ** current_level))

    @staticmethod
    async def get_user_upgrades(user_id: int) -> Dict[str, int]:
        upgrades = await Database.fetch(
            "SELECT upgrade_type, level FROM user_upgrades WHERE user_id = $1",
            user_id
        )
        return {row['upgrade_type']: row['level'] for row in upgrades}

    @staticmethod
    async def can_upgrade(user_id: int, upgrade_type: str) -> bool:
        if upgrade_type not in UpgradeService.UPGRADE_TYPES:
            return False

        current_level = await Database.fetchval(
            """
            SELECT level FROM user_upgrades 
            WHERE user_id = $1 AND upgrade_type = $2
            """,
            user_id, upgrade_type
        ) or 0

        if current_level >= UpgradeService.UPGRADE_TYPES[upgrade_type]['max_level']:
            return False

        cost = await UpgradeService.get_upgrade_cost(upgrade_type, current_level)
        user_balance = await Database.fetchval(
            "SELECT balance FROM users WHERE user_id = $1",
            user_id
        )

        return user_balance >= cost

    @staticmethod
    async def purchase_upgrade(user_id: int, upgrade_type: str) -> bool:
        if not await UpgradeService.can_upgrade(user_id, upgrade_type):
            return False

        current_level = await Database.fetchval(
            """
            SELECT level FROM user_upgrades 
            WHERE user_id = $1 AND upgrade_type = $2
            """,
            user_id, upgrade_type
        ) or 0

        cost = await UpgradeService.get_upgrade_cost(upgrade_type, current_level)
        tax = int(cost * (config.game.tax_percent / 100))
        total_cost = cost + tax

        # Start transaction
        async with Database.get_pool().acquire() as conn:
            async with conn.transaction():
                # Check balance again (in case it changed)
                user_balance = await conn.fetchval(
                    "SELECT balance FROM users WHERE user_id = $1",
                    user_id
                )

                if user_balance < total_cost:
                    return False

                # Update user balance
                await conn.execute(
                    "UPDATE users SET balance = balance - $1 WHERE user_id = $2",
                    total_cost, user_id
                )

                # Update or insert upgrade
                await conn.execute(
                    """
                    INSERT INTO user_upgrades (user_id, upgrade_type, level)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (user_id, upgrade_type) 
                    DO UPDATE SET level = user_upgrades.level + 1
                    """,
                    user_id, upgrade_type
                )

        return True

    @staticmethod
    async def get_upgrade_info(user_id: int) -> List[Dict]:
        user_upgrades = await UpgradeService.get_user_upgrades(user_id)
        result = []

        for upgrade_type, info in UpgradeService.UPGRADE_TYPES.items():
            current_level = user_upgrades.get(upgrade_type, 0)
            next_cost = await UpgradeService.get_upgrade_cost(upgrade_type, current_level)
            
            result.append({
                'type': upgrade_type,
                'name': info['name'],
                'current_level': current_level,
                'max_level': info['max_level'],
                'next_cost': next_cost,
                'can_upgrade': current_level < info['max_level']
            })

        return result 