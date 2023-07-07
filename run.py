import asyncio
import logging
import os

from dotenv import find_dotenv, load_dotenv
from yoyo import get_backend, read_migrations

from main import start

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename="bot.log", filemode="w")
    load_dotenv(find_dotenv())

    backend = get_backend(os.environ['PG_URI'])
    migrations = read_migrations('./migrations')

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    asyncio.run(start())
