import logging

logging.basicConfig(filename="/tmp/notifications.log", level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

import os
import socket
import json
from threading import Thread
from asyncio.exceptions import TimeoutError
import asyncio

from kde_connector.discovery import startDiscoveryServer
from kde_connector.service import startServiceServer
from kde_connector.notifications import notification_client

from kde_connector.storage import storage

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code one directory up
# or add the `decky-loader/plugin` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky_plugin


class Plugin:

    async def trust_device(self, device_id: str):
        decky_plugin.logger.info(f"Okay, {device_id} is trusted now")
        await storage.device_set_trusted(device_id, True)

    async def create_certificate(self, key, cert):
        import subprocess

        cert = f"{decky_plugin.DECKY_PLUGIN_RUNTIME_DIR}/cert.pem"
        key = f"{decky_plugin.DECKY_PLUGIN_RUNTIME_DIR}/key.pem"

        subprocess.check_call([
            "openssl", 
            "req", 
            "-x509", 
            "-newkey", 
            "rsa:4096", 
            "-keyout", 
            key, 
            "-out", 
            cert,
            "-sha256", 
            "-days", 
            "3650", 
            "-nodes", 
            "-subj", 
            "/C=US/O=KDE/OU=KDE Connect/CN=d0ff4c99_4eef_4300_b282_8345cad2b923"
        ])

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        decky_plugin.logger.info("Starting Deck Notifications")

        
        if not os.path.exists(cert):
            
    
        await storage.configure(f"{decky_plugin.DECKY_PLUGIN_RUNTIME_DIR}/db.sqlite3")
        await notification_client.configure()

        await asyncio.gather(
            asyncio.create_task(startDiscoveryServer()),
            asyncio.create_task(startServiceServer())
        )

        # openssl req -x509 -newkey rsa:4096 -keyout {key} -out {cert} -sha256 -days 3650 -nodes -subj "/C=US/O=KDE/OU=KDE Connect/CN=d0ff4c99_4eef_4300_b282_8345cad2b923"

    # Function called first during the unload process, utilize this to handle your plugin being removed
    async def _unload(self):
        decky_plugin.logger.info("Shuting down Deck Notifications!")
        await notification_client.shutdown()
        await storage.shutdown()

    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        pass
