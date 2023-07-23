import asyncpg
from typing import Sequence, Iterable


class DataBase:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def close_connection(self):
        await self.conn.close()

    async def add_merchant(self, data: dict) -> None:
        async with self.conn.transaction():
            await self.conn.execute(f"""
                INSERT INTO merchants(name, username, type, description, admin_username) VALUES
                ('{data['name']}', '{data['username']}', '{data['type']}',
                 '{data['description']}', '{data['admin_username']}');
            """)
            merchant_id = await self.get_merchant_id(data['name'])
            await self.add_merchant_countries(merchant_id, data['countries'])

    async def get_merchant_id(self, name: str) -> int:
        merchant_id: int = await self.conn.fetchval(f"""
            SELECT id FROM merchants
            WHERE name = '{name}';
        """)
        return merchant_id

    async def add_merchant_countries(self, merchant_id: int, countries: Sequence[str]) -> None:
        async with self.conn.transaction():
            for i in range(len(countries)):
                await self.conn.execute(f"""
                    INSERT INTO merchants_countries(merchant_id, country) VALUES 
                    ({merchant_id}, '{countries[i]}')
                """)

    async def add_trader(self, data: dict) -> None:
        async with self.conn.transaction():
            await self.conn.execute(f"""
                INSERT INTO traders(name, username, description, admin_username) VALUES
                ('{data['name']}', '{data['username']}', '{data['description']}', '{data['admin_username']}');
            """)
            trader_id = await self.get_trader_id(data['name'])
            await self.add_trader_countries(trader_id, data['countries'])

    async def get_trader_id(self, name: str) -> int:
        trader_id: int = await self.conn.fetchval(f"""
            SELECT id FROM traders
            WHERE name = '{name}';
        """)
        return trader_id

    async def add_trader_countries(self, trader_id: int, countries: Sequence[str]) -> None:
        async with self.conn.transaction():
            for i in range(len(countries)):
                await self.conn.execute(f"""
                    INSERT INTO traders_countries(trader_id, country) VALUES 
                    ({trader_id}, '{countries[i]}')
                """)

    async def merchants_by_country(self, country: str) -> list[tuple[str, str]]:
        results: Iterable[asyncpg.Record] = await self.conn.fetch(f"""
            SELECT name, type FROM merchants JOIN merchants_countries ON 
            merchants.id = merchants_countries.merchant_id
            WHERE country = '{country}' AND in_search
            ORDER BY type
        """)
        merchants = []
        for record in results:
            merchants.append((record['type'], record['name']))
        return merchants

    async def traders_by_country(self, country: str) -> list[str]:
        results: Iterable[asyncpg.Record] = await self.conn.fetch(f"""
            SELECT name FROM traders JOIN traders_countries tc on traders.id = tc.trader_id
            WHERE country = '{country}' AND in_search
        """)
        traders = []
        for record in results:
            traders.append(record['name'])
        return traders

    async def get_merchant_data(self, merchant_id: int) -> dict:
        async with self.conn.transaction():
            result: asyncpg.Record = await self.conn.fetchrow(f"""
                SELECT id, name, username, type, description, in_search, partner_id, admin_username
                FROM merchants WHERE merchants.id = {merchant_id};
            """)
            countries: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT country FROM merchants_countries 
                WHERE merchant_id = {merchant_id};
            """)
            merged_countries: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT country FROM merchants_countries WHERE
                merchant_id = {merchant_id} AND is_merged
            """)
        data = {
            'id': result['id'],
            'name': result['name'],
            'username': result['username'],
            'type': result['type'],
            'description': result['description'],
            'admin_username': result['admin_username'],
            'countries': [record['country'] for record in countries],
            'merged_countries': [record['country'] for record in merged_countries],
            'in_search': result['in_search'],
            'partner_id': result['partner_id'],
            'partner_name': None,
            'partner_username': None
        }
        partner = await self.get_partner_data(data['partner_id'], data['type'])
        if partner is not None:
            data['partner_name'] = partner[0]
            data['partner_username'] = partner[1]
        return data

    async def get_trader_data(self, trader_id: int) -> dict:
        async with self.conn.transaction():
            result: asyncpg.Record = await self.conn.fetchrow(f"""
                SELECT id, name, username, description, in_search, partner_id, admin_username
                FROM traders WHERE traders.id = {trader_id};
            """)
            countries: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT country FROM traders_countries 
                WHERE trader_id = {trader_id};
            """)
            merged_countries: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT country FROM traders_countries WHERE
                trader_id = {trader_id} AND is_merged
            """)
        data = {
            'id': result['id'],
            'name': result['name'],
            'username': result['username'],
            'type': "trader",
            'description': result['description'],
            'admin_username': result['admin_username'],
            'countries': [record['country'] for record in countries],
            'merged_countries': [record['country'] for record in merged_countries],
            'in_search': result['in_search'],
            'partner_id': result['partner_id'],
            'partner_name': None,
            'partner_username': None
        }
        partner = await self.get_partner_data(data['partner_id'], data['type'])
        if partner is not None:
            data['partner_name'] = partner[0]
            data['partner_username'] = partner[1]
        return data

    async def get_partner_data(self, partner_id: int, person_type: str) -> tuple[str, str] | None:
        if partner_id is None:
            return None
        if person_type == "trader":
            partner: asyncpg.Record = await self.conn.fetchrow(f"""
                SELECT name, username FROM merchants WHERE id = {partner_id}
            """)
        else:
            partner: asyncpg.Record = await self.conn.fetchrow(f"""
                SELECT name, username FROM traders WHERE id = {partner_id}
            """)
        return partner['name'], partner['username']

    async def delete_merchant(self, merchant_id: int) -> None:
        await self.conn.execute(f"""
            DELETE FROM merchants WHERE id = {merchant_id};
        """)

    async def delete_trader(self, trader_id: int) -> None:
        await self.conn.execute(f"""
            DELETE FROM traders WHERE id = {trader_id};
        """)

    async def delete_merchant_countries(self, merchant_id: int) -> None:
        await self.conn.execute(f"""
            DELETE FROM merchants_countries WHERE merchant_id = {merchant_id};
        """)

    async def delete_trader_countries(self, trader_id: int) -> None:
        await self.conn.execute(f"""
            DELETE FROM traders_countries WHERE trader_id = {trader_id};
        """)

    async def update_merchant(self, data: dict) -> None:
        if data['partner_id'] is None:
            await self.delete_merchant_countries(data['id'])
            await self.add_merchant_countries(data['id'], data['countries'])
        async with self.conn.transaction():
            await self.conn.execute(f"""
                UPDATE merchants SET name = '{data['name']}', username = '{data['username']}',
                description = '{data['description']}' WHERE id = {data['id']}
            """)

    async def update_trader(self, data: dict) -> None:
        if data['partner_id'] is None:
            await self.delete_trader_countries(data['id'])
            await self.add_trader_countries(data['id'], data['countries'])
        async with self.conn.transaction():
            await self.conn.execute(f"""
                UPDATE traders SET name = '{data['name']}', username = '{data['username']}',
                description = '{data['description']}' WHERE id = {data['id']}
            """)

    async def find_merchant_matches(self, merchant_id: int, partner_id: int | None) -> list[tuple[str, str]]:
        if partner_id is None:
            records = await self.conn.fetch(f"""
                SELECT t.name, tc.country FROM merchants m 
                JOIN merchants_countries mc on m.id = mc.merchant_id
                JOIN traders_countries tc on mc.country = tc.country
                JOIN traders t on tc.trader_id = t.id
                WHERE m.id = {merchant_id} AND t.partner_id IS NULL
                ORDER BY t.name, tc.country;
            """)
        else:
            records = await self.conn.fetch(f"""
                SELECT t.name, tc.country FROM merchants m 
                JOIN merchants_countries mc on m.id = mc.merchant_id
                JOIN traders_countries tc on mc.country = tc.country
                JOIN traders t on tc.trader_id = t.id
                WHERE m.id = {merchant_id} AND t.id = {partner_id} AND NOT tc.is_merged
                ORDER BY t.name, tc.country;
            """)
        match_traders = [(record['name'], record['country']) for record in records]
        return match_traders

    async def find_trader_matches(self, trader_id: int, partner_id: int | None) -> list[tuple[str, str, str]]:
        if partner_id is None:
            records = await self.conn.fetch(f"""
                SELECT m.type, m.name, mc.country FROM traders t 
                JOIN traders_countries tc on t.id = tc.trader_id
                JOIN merchants_countries mc on tc.country = mc.country
                JOIN merchants m on mc.merchant_id = m.id
                WHERE t.id = {trader_id} AND m.partner_id IS NULL
                ORDER BY m.type, m.name, mc.country;
            """)
        else:
            records = await self.conn.fetch(f"""
                SELECT m.type, m.name, mc.country FROM traders t 
                JOIN traders_countries tc on t.id = tc.trader_id
                JOIN merchants_countries mc on tc.country = mc.country
                JOIN merchants m on mc.merchant_id = m.id
                WHERE t.id = {trader_id} AND m.id = {partner_id} AND NOT mc.is_merged
                ORDER BY m.type, m.name, mc.country;
            """)
        match_merchants = [(record['type'], record['name'], record['country']) for record in records]
        return match_merchants

    async def add_match(self, merchant_id: int, trader_id: int, country: str) -> None:
        await self.conn.execute(f"""
            UPDATE merchants SET partner_id = {trader_id}
            WHERE id = {merchant_id};
            UPDATE traders SET partner_id = {merchant_id}
            WHERE id = {trader_id};
            UPDATE merchants_countries SET is_merged = TRUE
            WHERE merchant_id = {merchant_id} AND country = '{country}';
            UPDATE traders_countries SET is_merged = TRUE
            WHERE trader_id = {trader_id} AND country = '{country}';
        """)

    async def delete_match_country(self, merchant_id: int, trader_id: int, country: str) -> None:
        await self.conn.execute(f"""
            UPDATE merchants_countries SET is_merged = FALSE 
            WHERE merchant_id = {merchant_id} AND country = '{country}';
            UPDATE traders_countries SET is_merged = FALSE 
            WHERE trader_id = {trader_id} AND country = '{country}';
        """)

    async def delete_match(self, merchant_id: int, trader_id: int) -> None:
        await self.conn.execute(f"""
            UPDATE merchants SET partner_id = NULL
            WHERE id = {merchant_id};
            UPDATE traders SET partner_id = NULL
            WHERE id = {trader_id};
        """)

    async def merchant_in_search(self, in_search: bool, merchant_id: int) -> None:
        await self.conn.execute(f"""
            UPDATE merchants SET in_search = {in_search}
            WHERE id = {merchant_id};
        """)

    async def trader_in_search(self, in_search: bool, trader_id: int) -> None:
        await self.conn.execute(f"""
            UPDATE traders SET in_search = {in_search}
            WHERE id = {trader_id};
        """)

    async def search_by_username(self, username: str) -> tuple[int, str]:
        merchant_id: int | None = await self.conn.fetchval(f"""
            SELECT id FROM merchants WHERE username = '{username}';
        """)
        trader_id: int | None = await self.conn.fetchval(f"""
            SELECT id FROM traders WHERE username = '{username}';
        """)
        if merchant_id is not None:
            return merchant_id, 'merchant'
        return trader_id, 'trader'

    async def get_all_matches(self) -> list[Sequence[str]]:
        records = await self.conn.fetch(f"""
            SELECT merchants.name m_name, merchants.type, t.name t_name, tc.country  
             FROM merchants JOIN merchants_countries mc on merchants.id = mc.merchant_id
            JOIN traders_countries tc on mc.country = tc.country
            JOIN traders t on tc.trader_id = t.id
            WHERE merchants.in_search AND t.in_search AND merchants.in_search
            ORDER BY merchants.type, merchants.name, t.name, tc.country
        """)
        return [(record['type'], record['m_name'], record['t_name'], record['country']) for record in records]

    async def name_in_merchants(self, name: str) -> bool:
        query = f"SELECT name FROM merchants WHERE name = '{name}'"
        return len(await self.conn.fetch(query)) > 0

    async def username_in_merchants(self, username: str) -> bool:
        query = f"SELECT name FROM merchants WHERE username = '{username}'"
        return len(await self.conn.fetch(query)) > 0

    async def name_in_traders(self, name: str) -> bool:
        query = f"SELECT name FROM traders WHERE name = '{name}'"
        return len(await self.conn.fetch(query)) > 0

    async def username_in_traders(self, username: str) -> bool:
        query = f"SELECT name FROM traders WHERE username = '{username}'"
        return len(await self.conn.fetch(query)) > 0
