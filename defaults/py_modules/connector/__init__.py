import asyncio
import hashlib
import logging
import os
import platform
import uuid
from asyncio import QueueEmpty
from pathlib import Path

from .const import KDE_CONNECT_DISCOVERY_PORT, KDE_CONNECT_TCP_PORT, LOCAL_CERTIFICATE_FILE, HTTP_INTERNAL_PORT
from .discovery import DiscoveryProtocol
from .queue import event_queue
from .service import tcp_handler
from . import crypto
from .storage import storage


class ConnectorService:
    runtime_dir: Path
    fingerprint: str = None

    def __init__(self, runtime_dir):
        self.runtime_dir = Path(runtime_dir)

    async def local_fingerprint(self):
        if self.fingerprint:
            return self.fingerprint

        with open(LOCAL_CERTIFICATE_FILE, "rb") as f:
            local_cert_der = crypto.get_der_by_pem(f.read())

        local_public_key = await crypto.certificate_get_public_key(local_cert_der)
        self.fingerprint = hashlib.sha256(local_public_key).hexdigest()
        return self.fingerprint

    async def run(self):
        os.chdir(self.runtime_dir)

        device_id_file = Path("device_id.txt")
        if device_id_file.exists():
            with device_id_file.open("r") as f:
                device_id = f.read().strip()
        else:
            with device_id_file.open("w") as f:
                device_id = str(uuid.uuid4())
                f.write(device_id)

        # hostname
        device_name = platform.node()

        await storage.configure("db.sqlite3")

        if not os.path.exists(LOCAL_CERTIFICATE_FILE):
            await crypto.certificate_create(device_id)

        # UDP Discovery handler
        loop = asyncio.get_running_loop()
        await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(device_id, device_name),
            local_addr=('0.0.0.0', KDE_CONNECT_DISCOVERY_PORT),
        )

        # Main handler
        connect_server = await asyncio.start_server(
            tcp_handler,
            "0.0.0.0",
            KDE_CONNECT_TCP_PORT
        )

        await connect_server.start_serving()

        while True:
            await asyncio.sleep(1)

    async def get_event(self):
        try:
            return event_queue.get_nowait()
        except QueueEmpty:
            return None

    async def shutdown(self):
        await storage.shutdown()
