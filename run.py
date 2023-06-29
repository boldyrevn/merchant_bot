import asyncio
import logging

from dotenv import find_dotenv, load_dotenv

from main import start

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv(find_dotenv())
    asyncio.run(start())