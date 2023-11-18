from asyncio import StreamReader, StreamWriter

from connector.storage import Storage


class ConnectionContext:
    reader: StreamReader
    writer: StreamWriter

    storage: Storage

    device_id: str | None = None
    device_name: str | None = None
    remote_certificate: bytes | None = None
