import logging

logging.basicConfig(filename="/tmp/notifications.log", level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

import os
import socket
import json
from threading import Thread
from asyncio.exceptions import TimeoutError
import asyncio

from connector import ConnectorService, storage

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code one directory up
# or add the `decky-loader/plugin` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky_plugin


class Plugin:

    async def local_fingerprint(self):
        return await self._connector.local_fingerprint()

    async def device_list(self):
        return await storage.device_list()
    
    async def notification_list(self):
        return await storage.notification_list()

    async def trust_device(self, device_id: str, trust: bool = True):
        decky_plugin.logger.info(f"Okay, {device_id} is trusted now")
        await storage.device_set_trusted(device_id, trust)

    async def notifications_clear(self):
        await storage.notification_remove_all()

    async def get_event(self):
        return await self._connector.get_event()

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        decky_plugin.logger.info("Starting Deck Notifications")
        self._connector = ConnectorService(decky_plugin.DECKY_PLUGIN_RUNTIME_DIR)
        await self._connector.run()

    # Function called first during the unload process, utilize this to handle your plugin being removed
    async def _unload(self):
        decky_plugin.logger.info("Shuting down Deck Notifications!")
        await self._connector.shutdown()

    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        pass
