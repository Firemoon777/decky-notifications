import sqlite3
import logging
from pathlib import Path

from typing import *

logger = logging.getLogger("Storage")


class Storage:
    _trusted_cache: dict
    connection: sqlite3.Connection

    async def configure(self, path: Path):
        self._trusted_cache = dict()

        self.connection = sqlite3.connect(str(path))

        cur = self.connection.cursor()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS device ("
            "deviceId TEXT PRIMARY KEY, "
            "name TEXT, "
            "type TEXT, "
            "certificate BLOB, "
            "fingerprint TEXT, "
            "trusted INTEGER default 0"
            ")"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS notification ("
            "id TEXT PRIMARY KEY, "
            "title TEXT, "
            "body TEXT, "
            "appName TEXT, "
            "silent INTEGER, "
            "requestReplyId TEXT, "
            "time TIMESTAMP, "
            "icon TEXT"
            ")"
        )
        self.connection.commit()

    async def shutdown(self):
        self.connection.close()

    # device
    async def device_update(self, device_id: str, name: str, type: str):
        cur = self.connection.cursor()
        cur.execute(
            "INSERT INTO device(deviceId, name, type) values (?, ?, ?) "
            "ON CONFLICT (deviceId) DO UPDATE SET name=excluded.name, type=excluded.type",
            (device_id, name, type))
        self.connection.commit()

    async def device_set_certificate(self, device_id: str, certificate: bytes, fingerprint: str):
        cur = self.connection.cursor()
        cur.execute(
            "UPDATE device SET certificate = ?, fingerprint = ? WHERE deviceId = ?",
            (certificate, fingerprint, device_id)
        )
        self.connection.commit()

    async def device_get_certificate(self, device_id: str):
        cur = self.connection.cursor()
        res = cur.execute("SELECT certificate from device where deviceId = ?", (device_id,)).fetchone()

        return res[0] if res else None

    async def device_set_trusted(self, device_id: str, trusted: bool):
        self._trusted_cache.clear()

        cur = self.connection.cursor()
        cur.execute("UPDATE device SET trusted = ? WHERE deviceId = ?", (trusted, device_id))
        self.connection.commit()

    async def is_device_trusted(self, device_id: str) -> bool:
        if device_id in self._trusted_cache:
            logger.debug(f"device {device_id} is_trusted = {self._trusted_cache[device_id]} (cached)")
            return self._trusted_cache[device_id]

        cur = self.connection.cursor()
        res = cur.execute("SELECT trusted from device where deviceId = ?", (device_id,)).fetchone()

        if res is None:
            return False

        is_trusted = int(res[0]) == 1
        self._trusted_cache[device_id] = is_trusted

        return is_trusted

    async def device_list(self):
        cur = self.connection.cursor()
        res = cur.execute("SELECT deviceId, name, type, fingerprint, trusted from device").fetchall()

        result = list()
        for entry in res:
            result.append(dict(
                deviceId=entry[0],
                name=entry[1],
                type=entry[2],
                fingerprint=entry[3],
                is_trusted=entry[4]
            ))
        return result

    # notification
    async def notification_insert(
            self,
            id: str,
            title: str,
            body: str,
            appName: str,
            silent: bool,
            requestReplyId: str,
            time: int,
            icon: str = None
    ):
        cur = self.connection.cursor()

        cur.execute(
            "INSERT INTO notification(id, title, body, appName, silent, requestReplyId, time) "
            "values (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (id) DO UPDATE SET "
            "title=excluded.title, "
            "body=excluded.body, "
            "appName=excluded.appName, "
            "silent=excluded.silent, "
            "requestReplyId=excluded.requestReplyId, "
            "time=excluded.time",
            (id, title, body, appName, silent, requestReplyId, time)
        )

        if icon:
            cur.execute("UPDATE notification SET icon = ? WHERE id = ?", (icon, id))

        self.connection.commit()

    async def notification_get_icon(self, n_id):
        cur = self.connection.cursor()

        res = cur.execute(
            "SELECT icon FROM notification where id = ?",
            (n_id,)
        ).fetchone()

        if res is None:
            return None

        return res[0] or None

    async def notification_list(self):
        cur = self.connection.cursor()
        res = cur.execute(
            "SELECT id, title, body, appName, silent, requestReplyId, time, icon from notification order by time desc").fetchall()

        result = list()
        for entry in res:
            result.append(dict(
                id=entry[0],
                title=entry[1],
                body=entry[2],
                appName=entry[3],
                silent=entry[4],
                requestReplyId=entry[5],
                time=entry[6],
                icon=entry[7],
            ))
        return result

    async def notification_remove(self, id: str):
        cur = self.connection.cursor()
        cur.execute("DELETE FROM notification WHERE id = ?", (id,))
        self.connection.commit()

    async def notification_remove_all(self):
        cur = self.connection.cursor()
        cur.execute("DELETE FROM notification")
        self.connection.commit()


storage = Storage()
