"""
create database
"""

from yoyo import step

__depends__ = {}

steps = [
    step("""
        CREATE TABLE IF NOT EXISTS merchants(
            id SERIAL PRIMARY KEY,
            name VARCHAR(64),
            username VARCHAR(64),
            type VARCHAR(16),
            description TEXT,
            in_search BOOLEAN DEFAULT TRUE,
            partner_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS traders(
            id SERIAL PRIMARY KEY,
            name VARCHAR(64),
            username VARCHAR(64),
            description TEXT,
            in_search BOOLEAN DEFAULT TRUE,
            partner_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS merchants_countries(
            merchant_id INTEGER,
            country VARCHAR(32),
            is_merged BOOLEAN DEFAULT FALSE,
            PRIMARY KEY(merchant_id, country),
            FOREIGN KEY(merchant_id) REFERENCES merchants(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS traders_countries(
            trader_id INTEGER,
            country VARCHAR(32),
            is_merged BOOLEAN DEFAULT FALSE,
            PRIMARY KEY(trader_id, country),
            FOREIGN KEY(trader_id) REFERENCES traders(id) ON DELETE CASCADE
        );
    """, "DROP TABLE merchants, traders, merchants_countries, traders_countries CASCADE;")
]
