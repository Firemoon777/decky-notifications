import asyncio
import hashlib
import logging
import ssl
from dataclasses import dataclass
from enum import Enum
from typing import List

from connector import crypto
from connector.const import KDE_CONNECT_TCP_PORT, KDE_CONNECT_PROTOCOL_VERSION, LOCAL_CERTIFICATE_FILE, \
    LOCAL_PRIVATE_KEY_FILE, LOCAL_PUBLIC_KEY_FILE
from connector.context import ConnectionContext
from connector.packet.base import KDEConnectType, KDEPacketBase
from connector.packet.registry import registry


logger = logging.getLogger(__name__)


class KDEConnectDeviceType(str, Enum):
    DESKTOP = "desktop"
    LAPTOP = "laptop"
    PHONE = "phone"
    TABLET = "tablet"
    TV = "tv"


@dataclass
class KDEPacketIdentityBody:
    deviceId: str
    deviceName: str
    deviceType: KDEConnectDeviceType
    incomingCapabilities: List[str]
    outgoingCapabilities: List[str]
    protocolVersion: int = KDE_CONNECT_PROTOCOL_VERSION
    tcpPort: int = KDE_CONNECT_TCP_PORT


@dataclass
class KDEPacketIdentity(KDEPacketBase):
    body: KDEPacketIdentityBody

    type: KDEConnectType = KDEConnectType.IDENTITY

    @classmethod
    def me(cls, device_id: str, device_name):
        return cls(
            body=KDEPacketIdentityBody(
                deviceId=device_id,
                deviceName=device_name,
                deviceType=KDEConnectDeviceType.DESKTOP,
                incomingCapabilities=[
                    "kdeconnect.notification",
                    "kdeconnect.ping"
                ],
                outgoingCapabilities=[

                ]
            )
        )


@registry.register_handler(
    type=KDEConnectType.IDENTITY,
    clz=KDEPacketIdentity,
    only_trusted=False,
    ssl=False
)
async def identity_handler(packet: KDEPacketIdentity, context: ConnectionContext):
    # Upgrade connection to secure as client
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Using local certificates
    ssl_ctx.load_cert_chain(LOCAL_CERTIFICATE_FILE, keyfile=LOCAL_PRIVATE_KEY_FILE)

    # python's ssl can't properly handle untrusted self-signed certificates, disable it
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.VerifyMode.CERT_NONE

    # Create secure transport
    loop = asyncio.get_running_loop()
    transport = context.writer.transport
    protocol = transport.get_protocol()
    tls_transport = await loop.start_tls(transport, protocol, ssl_ctx, server_side=False)

    # hack: hot replace transport
    context.reader._transport = tls_transport
    context.writer._transport = tls_transport

    # Server MUST provide certificate, even if we didn't verify it
    ssl_obj: ssl.SSLObject | ssl.SSLSocket = context.writer.transport.get_extra_info("ssl_object")
    remote_cert_der = ssl_obj.getpeercert(True)

    # Save device info
    await context.storage.device_update(packet.body.deviceId, packet.body.deviceName, packet.body.deviceType)
    context.device_id = packet.body.deviceId
    context.device_name = packet.body.deviceName

    trusted = await context.storage.is_device_trusted(packet.body.deviceId)

    if trusted:
        # For trusted devices check certificate with saved one
        last_certificate = await context.storage.device_get_certificate(packet.body.deviceId)
        if last_certificate == remote_cert_der:
            context.remote_certificate = remote_cert_der
    else:
        # Update certificate only for untrusted devices
        remote_fingerprint = hashlib.sha256(remote_cert_der).hexdigest()
        await context.storage.device_set_certificate(packet.body.deviceId, remote_cert_der, remote_fingerprint)
        context.remote_certificate = remote_cert_der

