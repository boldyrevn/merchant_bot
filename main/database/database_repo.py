import asyncpg
from typing import Sequence


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
                ('{data['name']}', '{data['username']}', '{data['entity_type']}', '{data['description']}');
            """)
            merchant_id = await self.get_merchant_id(data['name'], data['username'])
            await self.add_merchant_countries(merchant_id, data['countries'])

    async def get_merchant_id(self, name: str, username: str) -> int:
        async with self.conn.transaction():
            merchant_id: int = await self.conn.fetchval(f"""
                SELECT id FROM merchants
                WHERE name = '{name}' AND username = '{username}';
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
            trader_id = await self.get_trader_id(data['name'], data['username'])
            await self.add_trader_countries(trader_id, data['countries'])

    async def get_trader_id(self, name: str, username: str) -> int:
        async with self.conn.transaction():
            trader_id: int = await self.conn.fetchval(f"""
                SELECT id FROM traders
                WHERE name = '{name}' AND username = '{username}';
            """)
        return trader_id

    async def add_trader_countries(self, trader_id: int, countries: Sequence[str]) -> None:
        async with self.conn.transaction():
            for i in range(len(countries)):
                await self.conn.execute(f"""
                    INSERT INTO traders_countries(trader_id, country) VALUES 
                    ({trader_id}, '{countries[i]}')
                """)
