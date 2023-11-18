import asyncio
import hashlib
import logging
import ssl
import time
from dataclasses import dataclass
from enum import Enum
from typing import List

from connector import crypto, event_queue
from connector.const import KDE_CONNECT_TCP_PORT, KDE_CONNECT_PROTOCOL_VERSION, LOCAL_CERTIFICATE_FILE, \
    LOCAL_PRIVATE_KEY_FILE, LOCAL_PUBLIC_KEY_FILE
from connector.context import ConnectionContext
from connector.packet.base import KDEConnectType, KDEPacketBase
from connector.packet.registry import registry


logger = logging.getLogger(__name__)


@dataclass
class KDEPacketPingBody:
    message: str | None = None


@dataclass
class KDEPacketPing(KDEPacketBase):
    body: KDEPacketPingBody

    type: KDEConnectType = KDEConnectType.PING


@registry.register_handler(
    type=KDEConnectType.PING,
    clz=KDEPacketPing
)
async def ping_handler(packet: KDEPacketPing, context: ConnectionContext):
    # Send event to frontend
    await event_queue.put({
        "event": "notification",
        "title": "KDE Connect ping",
        "body": packet.body.message or "Ping Message"
    })
