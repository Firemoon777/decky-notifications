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
class KDEPacketPairBody:
    pair: bool


@dataclass
class KDEPacketPair(KDEPacketBase):
    body: KDEPacketPairBody

    type: KDEConnectType = KDEConnectType.PAIR

    @classmethod
    def create(cls, pair: bool):
        return cls(
            body=KDEPacketPairBody(
                pair=pair
            )
        )


@registry.register_handler(
    type=KDEConnectType.PAIR,
    clz=KDEPacketPair,
    only_trusted=False
)
async def pair_handler(packet: KDEPacketPair, context: ConnectionContext):
    if packet.body.pair is False:
        await context.storage.device_set_trusted(context.device_id, False)
        logger.debug(f"{context.device_id} cancelled pairing!")
        return

    # Calculate remote public key
    remote_public_key = await crypto.certificate_get_public_key(context.remote_certificate)

    # Read local certificate
    with open(LOCAL_CERTIFICATE_FILE, "rb") as f:
        local_cert_der = crypto.get_der_by_pem(f.read())
    local_public_key = await crypto.certificate_get_public_key(local_cert_der)

    # Calculate verification key
    a, b = local_public_key, remote_public_key
    if a < b:
        a, b = b, a
    verification_key = hashlib.sha256(a + b).hexdigest()
    logger.debug(f"Verification key: {verification_key}")

    # Send event to frontend
    await event_queue.put({
        "event": "pair",
        "deviceId": context.device_id,
        "deviceName": context.device_name,
        "verificationKey": verification_key
    })

    # Wait for approval
    timeout = time.time() + 30
    while time.time() < timeout:

        is_now_trusted = await context.storage.is_device_trusted(context.device_id)
        logger.info(f"{context.device_name} is trusted={is_now_trusted}")
        if is_now_trusted:
            p = KDEPacketPair.create(True)
            context.writer.write(p.bytes())
            await context.writer.drain()
            logger.info(f"Sending pair=True to {context.device_name}")
            return

        await asyncio.sleep(1)

    logger.warning(f"Pairing {context.device_name} timeout")
