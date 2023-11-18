import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

from connector import ConnectorService


async def main():
    await ConnectorService("runtime").run()

if __name__ == "__main__":
    asyncio.run(main())
