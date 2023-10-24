import asyncio

from .packet import Packet, KDEConnectType

DISCOVERY_PORT = 1716

class DiscoveryProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        r = Packet.from_bytes(data)
        p = Packet.identity()

        if r.type != KDEConnectType.IDENTITY:
            return

        if r.body["deviceId"] == p.body["deviceId"]:
            return

        self.transport.sendto(p.bytes(), ("255.255.255.255", DISCOVERY_PORT))


async def startDiscoveryServer():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DiscoveryProtocol(),
        local_addr=('0.0.0.0', 1716),
        reuse_port=True,
        allow_broadcast=True
    )

    while True:
        await asyncio.sleep(1)
