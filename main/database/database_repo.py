import asyncpg
from typing import Sequence, Iterable


class DataBase:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def init(self) -> None:
        async with self.conn.transaction():
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS merchants(
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(64),
                    username VARCHAR(64),
                    type VARCHAR(16),
                    description TEXT,
                    in_search BOOLEAN DEFAULT TRUE
                );
                CREATE TABLE IF NOT EXISTS traders(
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(64),
                    username VARCHAR(64),
                    description TEXT,
                    in_search BOOLEAN DEFAULT TRUE
                );
                CREATE TABLE IF NOT EXISTS matches(
                    merchant_id INTEGER,
                    trader_id INTEGER,
                    PRIMARY KEY(merchant_id, trader_id),
                    FOREIGN KEY(merchant_id) REFERENCES merchants(id) ON DELETE CASCADE,
                    FOREIGN KEY(trader_id) REFERENCES traders(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS merchants_countries(
                    merchant_id INTEGER,
                    country VARCHAR(32),
                    PRIMARY KEY(merchant_id, country),
                    FOREIGN KEY(merchant_id) REFERENCES merchants(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS traders_countries(
                    trader_id INTEGER,
                    country VARCHAR(32),
                    PRIMARY KEY(trader_id, country),
                    FOREIGN KEY(trader_id) REFERENCES traders(id) ON DELETE CASCADE
                );
            """)

    async def close_connection(self):
        await self.conn.close()

    async def add_merchant(self, data: dict) -> None:
        async with self.conn.transaction():
            await self.conn.execute(f"""
                INSERT INTO merchants(name, username, type, description) VALUES
                ('{data['name']}', '{data['username']}', '{data['type']}',
                 '{data['description']}');
            """)
            merchant_id = await self.get_merchant_id(data['name'])
            await self.add_merchant_countries(merchant_id, data['countries'])

    async def get_merchant_id(self, name: str) -> int:
        async with self.conn.transaction():
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
                INSERT INTO traders(name, username, description) VALUES
                ('{data['name']}', '{data['username']}', '{data['description']}');
            """)
            trader_id = await self.get_trader_id(data['name'])
            await self.add_trader_countries(trader_id, data['countries'])

    async def get_trader_id(self, name: str) -> int:
        async with self.conn.transaction():
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
        async with self.conn.transaction():
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
        async with self.conn.transaction():
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
                SELECT id, name, username, type, description, in_search 
                FROM merchants WHERE merchants.id = {merchant_id};
            """)
            countries: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT country FROM merchants_countries 
                WHERE merchant_id = {merchant_id};
            """)
            partners: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT name, username FROM matches JOIN traders t on matches.trader_id = t.id
                WHERE merchant_id = {merchant_id};
            """)
        data = {
            'id': result['id'],
            'name': result['name'],
            'username': result['username'],
            'type': result['type'],
            'description': result['description'],
            'countries': [record['country'] for record in countries],
            'partners': [(record['name'], record['username']) for record in partners],
            'in_search': result['in_search']
        }
        return data

    async def get_trader_data(self, trader_id: int) -> dict:
        async with self.conn.transaction():
            result: asyncpg.Record = await self.conn.fetchrow(f"""
                SELECT id, name, username, description, in_search
                FROM traders WHERE traders.id = {trader_id};
            """)
            countries: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT country FROM traders_countries 
                WHERE trader_id = {trader_id};
            """)
            partners: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT name, username FROM matches JOIN merchants m on matches.merchant_id = m.id
                WHERE trader_id = {trader_id};
            """)
        data = {
            'id': result['id'],
            'name': result['name'],
            'username': result['username'],
            'type': "trader",
            'description': result['description'],
            'countries': [record['country'] for record in countries],
            'partners': [(record['name'], record['username']) for record in partners],
            'in_search': result['in_search']
        }
        return data

    async def delete_merchant(self, merchant_id: int) -> None:
        async with self.conn.transaction():
            await self.conn.execute(f"""
                DELETE FROM merchants WHERE id = {merchant_id};
            """)

    async def delete_trader(self, trader_id: int) -> None:
        async with self.conn.transaction():
            await self.conn.execute(f"""
                DELETE FROM traders WHERE id = {trader_id};
            """)

    async def delete_merchant_countries(self, merchant_id: int) -> None:
        async with self.conn.transaction():
            await self.conn.execute(f"""
                DELETE FROM merchants_countries WHERE merchant_id = {merchant_id};
            """)

    async def delete_trader_countries(self, trader_id: int) -> None:
        async with self.conn.transaction():
            await self.conn.execute(f"""
                DELETE FROM traders_countries WHERE trader_id = {trader_id};
            """)

    async def update_merchant(self, data: dict) -> None:
        await self.delete_merchant_countries(data['id'])
        await self.add_merchant_countries(data['id'], data['countries'])
        async with self.conn.transaction():
            await self.conn.execute(f"""
                UPDATE merchants SET name = '{data['name']}', username = '{data['username']}',
                description = '{data['description']}' WHERE id = {data['id']}
            """)

    async def update_trader(self, data: dict) -> None:
        await self.delete_trader_countries(data['id'])
        await self.add_trader_countries(data['id'], data['countries'])
        async with self.conn.transaction():
            await self.conn.execute(f"""
                UPDATE traders SET name = '{data['name']}', username = '{data['username']}',
                description = '{data['description']}' WHERE id = {data['id']}
            """)

    async def find_merchant_matches(self, merchant_id: int) -> list[tuple[str, str]]:
        async with self.conn.transaction():
            records = await self.conn.fetch(f"""
                SELECT name, tc.country FROM merchants_countries 
                JOIN traders_countries tc on merchants_countries.country = tc.country
                JOIN traders t on tc.trader_id = t.id
                WHERE merchant_id = {merchant_id} AND in_search AND trader_id NOT IN (
                    SELECT matches.trader_id FROM matches
                    WHERE matches.merchant_id = {merchant_id} 
                )
                ORDER BY tc.country, name;
            """)
        match_traders = [(record['country'], record['name']) for record in records]
        return match_traders

    async def find_trader_matches(self, trader_id: int) -> list[tuple[str, str, str]]:
        async with self.conn.transaction():
            records = await self.conn.fetch(f"""
                SELECT type, name, mc.country FROM traders_countries
                JOIN merchants_countries mc on traders_countries.country = mc.country
                JOIN merchants m on mc.merchant_id = m.id
                WHERE trader_id = {trader_id} AND in_search AND merchant_id NOT IN (
                    SELECT matches.merchant_id FROM matches
                    WHERE matches.trader_id = {trader_id}
                )
                ORDER BY type, name, mc.country;
            """)
        match_merchants = [(record['type'], record['name'], record['country']) for record in records]
        return match_merchants

    async def add_match(self, merchant_id: int, trader_id: int) -> None:
        async with self.conn.transaction():
            await self.conn.execute(f"""
                INSERT INTO matches(merchant_id, trader_id) VALUES 
                ({merchant_id}, {trader_id});
            """)

    async def delete_match(self, merchant_id: int, trader_id: int) -> None:
        if merchant_id is None or trader_id is None:
            return
        async with self.conn.transaction():
            await self.conn.execute(f"""
                DELETE FROM matches WHERE trader_id = {trader_id} AND merchant_id = {merchant_id};
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

    async def get_all_matches(self) -> list[tuple[str, str, str]]:
        records: list[asyncpg.Record] = await self.conn.fetch(f"""
            SELECT type, merchants.name merchant, t.name trader 
            FROM merchants JOIN matches m on merchants.id = m.merchant_id
            JOIN traders t on m.trader_id = t.id
        """)
        return [(record['type'], record['merchant'], record['trader']) for record in records]
