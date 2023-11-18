import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Callable


class KDEConnectType(str, Enum):
    UNKNOWN = "unknown"

    IDENTITY = "kdeconnect.identity"
    PAIR = "kdeconnect.pair"

    PING = "kdeconnect.ping"

    NOTIFICAION = "kdeconnect.notification"
    NOTIFICAION_ACTION = "kdeconnect.notification.action"
    NOTIFICAION_REPLY = "kdeconnect.notification.reply"

    def __str__(self):
        return str(self.value)

    @staticmethod
    def from_str(data: str):
        try:
            return KDEConnectType(data)
        except ValueError:
            return KDEConnectType.UNKNOWN


@dataclass
class KDEPacketBase:
    body: dict

    type: KDEConnectType

    id: int = field(default_factory=lambda: int(time.time() * 1000))

    payloadSize: int | None = None
    payloadTransferInfo: dict | None = None

    def dict(self):
        def factory(x) -> dict:
            """
            Official KDE Connect clients (for Android at least) disrespects `None` in optional fields.
            For example, if `payloadTransferInfo` is present and `None`,
            exception will be thrown and packet dropped

            Implement custom factory drops `None` fields
            """
            return {k: v for (k, v) in x if v is not None}
        return asdict(self, dict_factory=factory)

    def json(self, **kwargs):
        return json.dumps(self.dict(), **kwargs) + "\n"

    def bytes(self):
        return self.json().encode(encoding="utf-8")
