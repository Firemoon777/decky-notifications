import sqlite3
import logging

from typing import *

logger = logging.getLogger("Storage")


class Storage:

    _trusted: dict
    
    async def configure(self, path):
        self._trusted = dict()

        self.connection = sqlite3.connect(path)

        cur = self.connection.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS device (deviceId TEXT PRIMARY KEY, name TEXT, type TEXT, trusted INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS notification (id TEXT PRIMARY KEY, title TEXT, body TEXT, appName TEXT, silent INTEGER, requestReplyId TEXT, time TIMESTAMP)")
        self.connection.commit()

    async def shutdown(self):
        self.connection.close()

    # device
    async def device_update(self, device_id: str, name: str, type: str):
        cur = self.connection.cursor()
        cur.execute("INSERT OR REPLACE INTO device(deviceId, name, type, trusted) values (?, ?, ?, FALSE)", (device_id, name, type))
        self.connection.commit()

    async def device_set_trusted(self, device_id: str, trusted: bool):
        self._trusted.clear()

        cur = self.connection.cursor()
        cur.execute("UPDATE device SET trusted = ? WHERE deviceId = ?", (trusted, device_id))
        self.connection.commit()

    async def is_device_trusted(self, device_id: str) -> bool:
        if device_id in self._trusted:
            logger.info(f">>>>>>> Trust device {device_id}: {self._trusted[device_id]} (cached)")
            return self._trusted[device_id]
        
        cur = self.connection.cursor()
        res = cur.execute("SELECT trusted from device where deviceId = ?", (device_id,)).fetchone()

        logger.info(f">>>>>>>> Trust device {device_id}: {res}")

        if res is None:
            return False
        
        is_trusted = int(res[0]) == 1
        self._trusted[device_id] = is_trusted

        return is_trusted
    
    async def device_list(self):
        cur = self.connection.cursor()
        res = cur.execute("SELECT deviceId, name, type, trusted from device").fetchall()

        result = list()
        for entry in res:
            result.append(dict(
                deviceId=entry[0],
                name=entry[1],
                type=entry[2],
                is_trusted=entry[3]
            ))
        return result
    
    # notification
    async def notification_insert(self, id: str, title: str, body: str, appName: str, silent: bool, requestReplyId: str, time: int):
        cur = self.connection.cursor()

        cur.execute(
            "INSERT OR REPLACE INTO notification(id, title, body, appName, silent, requestReplyId, time) values (?, ?, ?, ?, ?, ?, ?)", 
            (id, title, body, appName, silent, requestReplyId, time)
        )

        self.connection.commit() 

    async def notification_remove(self, id: str):
        cur = self.connection.cursor()
        cur.execute("DELETE FROM notification WHERE id = ?", (id,))
        self.connection.commit()


storage = Storage()