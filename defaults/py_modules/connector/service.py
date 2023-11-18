from asyncio import StreamReader, StreamWriter

from connector.storage import storage
from connector.context import ConnectionContext
from connector.packet.registry import registry

from connector.packet.handler import identity, pair, ping, notification


async def tcp_handler(reader: StreamReader, writer: StreamWriter):
    context = ConnectionContext()
    context.reader = reader
    context.writer = writer
    context.storage = storage

    while True:
        data = await reader.readline()

        # EOF check
        if not data:
            return

        await registry.handle_packet(data, context=context)
