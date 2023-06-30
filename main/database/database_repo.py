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
                    description TEXT
                );
                CREATE TABLE IF NOT EXISTS traders(
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(64),
                    username VARCHAR(64),
                    description TEXT
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
                ('{data['name']}', '{data['username']}', '{data['type']}', '{data['description']}');
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
                WHERE country = '{country}'
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
                WHERE country = '{country}'
            """)
        traders = []
        for record in results:
            traders.append(record['name'])
        return traders

    async def get_merchant_data(self, merchant_id: int) -> dict:
        async with self.conn.transaction():
            result: asyncpg.Record = await self.conn.fetchrow(f"""
                SELECT id, name, username, type, description 
                FROM merchants WHERE merchants.id = {merchant_id};
            """)
            countries: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT country FROM merchants_countries 
                WHERE merchant_id = {merchant_id};
            """)
            partners: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT name FROM matches JOIN traders t on matches.trader_id = t.id
                WHERE merchant_id = {merchant_id};
            """)
        data = {
            'id': result['id'],
            'name': result['name'],
            'username': result['username'],
            'type': result['type'],
            'description': result['description'],
            'countries': [record['country'] for record in countries],
            'partners': [record['name'] for record in partners]
        }
        return data

    async def get_trader_data(self, trader_id: int) -> dict:
        async with self.conn.transaction():
            result: asyncpg.Record = await self.conn.fetchrow(f"""
                SELECT id, name, username, description 
                FROM traders WHERE traders.id = {trader_id};
            """)
            countries: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT country FROM traders_countries 
                WHERE trader_id = {trader_id};
            """)
            partners: list[asyncpg.Record] = await self.conn.fetch(f"""
                SELECT name FROM matches JOIN merchants m on matches.merchant_id = m.id
                WHERE trader_id = {trader_id};
            """)
        data = {
            'id': result['id'],
            'name': result['name'],
            'username': result['username'],
            'type': "trader",
            'description': result['description'],
            'countries': [record['country'] for record in countries],
            'partners': [record['name'] for record in partners]
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



