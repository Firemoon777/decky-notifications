import time
import json
import asyncio
from asyncio import transports
from ssl import SSLContext
import base64

from .packet import Packet, KDEConnectType
from .notifications import notification_client
from .storage import storage

import decky_plugin

import logging


logger = logging.getLogger("service")


async def tcp_handler(reader, writer):
    device = None
    device_id = None

    while True:
        data = (await reader.readline()).strip()

        if not data:
            break

        try:
            p = Packet.from_bytes(data)

            if p.type == KDEConnectType.IDENTITY:
                await storage.device_update(p.body["deviceId"], p.body["deviceName"], p.body["deviceType"])
                device = {
                    "id": p.body["deviceId"],
                    "name": p.body["deviceName"],
                    "type": p.body["deviceType"]
                }
                device_id = device["id"]
                logger.info(f"Device {device} connected")

                ssl = SSLContext()
                decky_plugin.logger.info(f"cert: {decky_plugin.DECKY_PLUGIN_RUNTIME_DIR}")
                ssl.load_cert_chain(f"{decky_plugin.DECKY_PLUGIN_RUNTIME_DIR}/cert.pem", f"{decky_plugin.DECKY_PLUGIN_RUNTIME_DIR}/key.pem")

                transport = writer.transport
                protocol = transport.get_protocol()
                loop = asyncio.get_running_loop()
                transport = await loop.start_tls(transport, protocol, ssl)
                reader._transport = transport
                writer._transport = transport

                response = Packet.identity()
                writer.write(response.bytes())

            if not device_id:
                break

            if p.type == KDEConnectType.PAIR:
                suggestion = p.body.get("pair", False)
                
                logger.info(f"Device {device} send pair={suggestion}")

                if suggestion is True:
                    await notification_client.sendPairingRequest(dict(
                        key="some-fingerprint",
                        **device
                    ))

                    waiting_time = time.time() + 30

                    while time.time() < waiting_time:
                        if await storage.is_device_trusted(device_id):
                            logger.info(f"User accepted pairing with {device}!")
                            break
                        await asyncio.sleep(1)

                    if await storage.is_device_trusted(device_id):
                        response = Packet.pair(True)
                        writer.write(response.bytes())
                        continue

                logger.info(f"Pairing with {device} dodged")
                    
                await storage.device_set_trusted(device_id, False)
                response = Packet.pair(False)
                writer.write(response.bytes())

            if storage.is_device_trusted(device_id) is False:
                response = Packet.pair(False)
                writer.write(response.bytes())
                continue

            if p.type == KDEConnectType.PING:
                pass

            if p.type == KDEConnectType.NOTIFICAION:
                n_id = p.body["id"]
                if "isCancel" in p.body:
                    # await storage.notification_remove(n_id)
                    continue

                title = p.body["title"]
                body = p.body["text"]
                appName = p.body["appName"]
                silent = p.body.get("silent", True)
                icon = None

                logger.info(p.dict())
                if p.payloadSize:
                    logger.info("Found additional payload!")
                    logger.info(f"Payload data: {p.payloadTransferInfo}")

                    addr = reader._transport.get_extra_info('peername')[0]
                    port = p.payloadTransferInfo["port"]
                    logger.info(f"Data downloading from {addr}:{port}")

                    data_ssl = SSLContext()
                    data_ssl.load_cert_chain(f"{decky_plugin.DECKY_PLUGIN_RUNTIME_DIR}/cert.pem", f"{decky_plugin.DECKY_PLUGIN_RUNTIME_DIR}/key.pem")
                    
                    data_reader, data_writer = await asyncio.open_connection(addr, port, ssl=data_ssl)
                    out_data = p.body["payloadHash"].encode()
                    logger.info(f"Connection estabilished, sending: {out_data} on {data_writer}")
                    if data_writer:
                        data_writer.write(out_data)
                    data = await data_reader.read(p.payloadSize)
                    logger.info(f"Downloaded {len(data)} bytes ({data[:5]})")

                    icon_b64 = base64.b64encode(data)
                    icon = f"data:image/png;base64,{icon_b64.decode()}"

                    data_writer.close()

                    logger.info("Downloaded file")


                await storage.notification_insert(
                    n_id,
                    title,
                    body,
                    appName,
                    silent,
                    p.body.get("requestReplyId"),
                    p.body.get("time")
                )

                if not silent:
                    await notification_client.send_notification(title, body, icon)

            await writer.drain()
        except Exception as e:
            decky_plugin.logger.exception(e)

        logger.info(f"Device {device_id} disconnected")


class ServiceConnectProtocol(asyncio.Protocol):
    def __init__(self, loop):
        self.loop = loop

    def connection_made(self, transport: asyncio.Transport) -> None:
        decky_plugin.logger.info(f"Connection made")
        self.transport = transport
    
    def data_received(self, data: bytes) -> None:
        self.loop.create_task(self.data_received_async(data))

    async def data_received_async(self, data: bytes) -> None:
        p = Packet.from_bytes(data)
        try:
            #p = Packet.from_bytes(data)
            decky_plugin.logger.info(f"TCP Data: {p}")

            if p.type == KDEConnectType.IDENTITY:
                ssl = SSLContext()
                ssl.load_cert_chain("/home/deck/homebrew/plugins/Decky-Notifications/cert.pem", "/home/deck/homebrew/plugins/Decky-Notifications/key.pem")

                await self.loop.start_tls(self.transport, self, ssl)

                response = Packet.identity()
                self.transport.write(response.bytes())
                decky_plugin.logger.info(f"Identity response: {response.json()}")

            
        except Exception as e:
            decky_plugin.logger.info(f"[{e}] Raw TCP Data: {data}")
            
        return super().data_received(data)
    
    def connection_lost(self, exc: Exception | None) -> None:
        decky_plugin.logger.info(f"Connection lost: {exc}")
        return super().connection_lost(exc)
    

async def startServiceServer():
    server = await asyncio.start_server(
        #lambda: ServiceConnectProtocol(loop),
        tcp_handler,
        "0.0.0.0",
        1717,
        reuse_port=True,
    )

    async with server:
        await server.serve_forever()