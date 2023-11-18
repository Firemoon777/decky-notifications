import asyncio
import base64
import hashlib
import logging
import ssl
import time
from dataclasses import dataclass, field
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
class KDEPacketNotificationBody:
    id: str
    appName: str = None
    ticker: str = None
    text: str = None
    title: str = None
    payloadHash: str = None
    actions: List[str] = field(default_factory=list)
    requestReplyId: str = None
    time: str = None
    onlyOnce: bool = False
    silent: bool = False
    isClearable: bool = True
    isCancel: bool = False


@dataclass
class KDEPacketNotification(KDEPacketBase):
    body: KDEPacketNotificationBody

    type: KDEConnectType = KDEConnectType.NOTIFICAION


@registry.register_handler(
    type=KDEConnectType.NOTIFICAION,
    clz=KDEPacketNotification
)
async def notification_handler(packet: KDEPacketNotification, context: ConnectionContext):
    # Notification was canceled -- remove it
    if packet.body.isCancel:
        await context.storage.notification_remove(packet.body.id)
        return

    # Ignore sticky notifications
    if packet.body.isClearable is False:
        return

    icon = None

    # Notification contains image
    if packet.payloadSize is not None:
        logger.debug(f"Additional payload found!")

        remote_addr = context.reader._transport.get_extra_info("peername")[0]
        remote_port = packet.payloadTransferInfo["port"]

        logger.debug(f"Downloading from {remote_addr}:{remote_port}")

        ssl_context = ssl.SSLContext()
        # Enable certificate verification
        ssl_context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
        # Load our certificates: remote host will check it
        ssl_context.load_cert_chain(LOCAL_CERTIFICATE_FILE, LOCAL_PRIVATE_KEY_FILE)
        # Load remote certificate as trusted
        ssl_context.load_verify_locations(cadata=context.remote_certificate)

        payload_reader, payload_writer = await asyncio.open_connection(remote_addr, remote_port, ssl=ssl_context)

        # Request payload by sending payloadHash
        payload_writer.write(packet.body.payloadHash.encode())
        await payload_writer.drain()

        # Seems to be PNG every time
        data = await payload_reader.read(packet.payloadSize)

        # Anyway browser will display it
        icon = f"data:image/png;base64,{base64.b64encode(data).decode()}"

    # Save notification in storage
    await context.storage.notification_insert(
        packet.body.id,
        packet.body.title,
        packet.body.text,
        packet.body.appName,
        packet.body.silent,
        packet.body.requestReplyId,
        int(packet.body.time),
        icon
    )

    if packet.body.silent is False:
        if not icon:
            icon = await context.storage.notification_get_icon(packet.body.id)

        # Send event to frontend
        await event_queue.put({
            "event": "notification",
            "title": f"[{packet.body.appName}] {packet.body.title}",
            "body": packet.body.text,
            "icon": icon
        })
