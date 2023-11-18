from enum import Enum
import time
import json


# class Packet:
#     id: int
#     type: KDEConnectType
#     body: dict
#
#     payloadSize: int
#     payloadTransferInfo: dict
#
#     def __init__(self, type, body=None):
#         self.id = int(time.time() * 1000)
#         self.type = type
#         self.body = body or dict()
#
#     def dict(self):
#         return dict(
#             id=self.id,
#             type=str(self.type),
#             body=self.body,
#         )
#
#     def json(self):
#         return json.dumps(self.dict()) + "\n"
#
#     def bytes(self):
#         out = self.json()
#         return out.encode()
#
#     def __str__(self):
#         return f"Packet<type={self.type}, body={self.body}>"
#
#     @staticmethod
#     def from_bytes(data: bytes):
#         data_str = data.decode(errors='ignore')
#         data_json = json.loads(data_str)
#
#         result = Packet(None)
#
#         result.id = int(data_json["id"])
#         result.type = KDEConnectType.from_str(data_json["type"])
#         result.body = data_json["body"]
#
#         result.payloadSize = data_json.get("payloadSize")
#         result.payloadTransferInfo = data_json.get("payloadTransferInfo")
#
#         return result
#
#     @staticmethod
#     def identity():
#         body = {
#             "deviceId": "d0ff4c99_4eef_4300_b282_8345cad2b923",
#             "deviceName": "KDE Connect Emulator",
#             "protocolVersion": PROTOCOL_VERSION,
#             "deviceType": "desktop",
#             "incomingCapabilities": [
#                 "kdeconnect.notification",
#                 "kdeconnect.ping"
#             ],
#             "outgoingCapabilities": [
#                 "kdeconnect.ping"
#             ],
#             "tcpPort": 1717,
#
#         }
#         return Packet(KDEConnectType.IDENTITY, body)
#
#     @staticmethod
#     def pair(pair: bool):
#         body = {
#             "pair": pair
#         }
#         return Packet(KDEConnectType.PAIR, body)
