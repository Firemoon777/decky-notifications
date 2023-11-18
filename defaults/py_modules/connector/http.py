from asyncio import StreamReader, StreamWriter


async def http_handler(reader: StreamReader, writer: StreamWriter):
    while True:
        data = await reader.readline()

        # EOF check
        if not data:
            return

        print(data)