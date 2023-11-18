import json
import logging
from typing import Callable, Type, Dict

from connector.context import ConnectionContext
from connector.packet.base import KDEPacketBase


logger = logging.getLogger(__name__)


class PacketRegistry:
    _packet_map: dict[str, Dict] = dict()

    def register_handler(self, type: str, clz: Type, ssl: bool = True, only_trusted: bool = True):
        def wrapper(func):
            if type in self._packet_map:
                raise RuntimeError(f"Packet type '{type}' already has registered handler!")
            self._packet_map[type] = {
                "func": func,
                "clz": clz,
                "ssl": ssl,
                "only_trusted": only_trusted
            }
        return wrapper

    async def handle_packet(self, data: bytes, context: ConnectionContext):
        payload = json.loads(data.decode(encoding="utf-8", errors="ignore"))
        base_packet = KDEPacketBase(**payload)

        logger.debug(f"Received {base_packet.type} from {context.device_name}")
        if base_packet.type not in self._packet_map:
            logger.warning(f"Unsupported packet type: {base_packet.type}! Dropping...")
            return None

        if self._packet_map[base_packet.type]["ssl"] and context.remote_certificate is None:
            logger.warning(f"Packet '{base_packet.type}' should be sent in SSL Channel!")
            return None

        if self._packet_map[base_packet.type]["only_trusted"]:
            if not context.device_id:
                logger.warning(f"Packet '{base_packet.type}' sent from unknown device!")
                return None

            trusted = await context.storage.is_device_trusted(context.device_id)
            if not trusted:
                logger.warning(f"Packet '{base_packet.type}' sent from untrusted device '{context.device_id}'!")

                from .handler.pair import KDEPacketPair
                unpair_packet = KDEPacketPair.create(False)
                context.writer.write(unpair_packet.bytes())
                await context.writer.drain()
                return

        clz = self._packet_map[base_packet.type]["clz"]
        func = self._packet_map[base_packet.type]["func"]
        packet = clz(**payload)
        try:
            packet.body = packet.__annotations__["body"](**packet.body)
        except Exception as e:
            logger.exception(e)

        return await func(packet, context=context)


registry = PacketRegistry()
