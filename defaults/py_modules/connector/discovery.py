import asyncio
import json
import logging

from .const import KDE_CONNECT_DISCOVERY_PORT
from .packet.base import KDEConnectType, KDEPacketBase
from connector.packet.handler.identity import KDEPacketIdentity


logger = logging.getLogger(__name__)


class DiscoveryProtocol(asyncio.DatagramProtocol):
    transport = None
    device_id: str
    device_name: str

    def __init__(self, device_id: str, device_name: str):
        self.device_id = device_id
        self.device_name = device_name

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        packet = KDEPacketBase(**json.loads(data.decode(encoding="utf-8", errors="ignore")))

        # Ignore all except IDENTITY packets
        if packet.type != KDEConnectType.IDENTITY:
            return

        logger.debug(f"UDP Received from {addr}: {packet}")

        # Normally we should connect to sender through TCP,
        # but python's ssl cannot verify self-signed certificates.
        #
        # Workaround: answer with ours IDENTITY to force remote device initiate TCP connection
        #
        # It breaks Steam Deck to Steam Deck communication. But who cares?
        response = KDEPacketIdentity.me(self.device_id, self.device_name)
        logger.debug(f"Answer to {(addr[0], KDE_CONNECT_DISCOVERY_PORT)}: {response.json()}")
        self.transport.sendto(response.bytes(), (addr[0], KDE_CONNECT_DISCOVERY_PORT))
