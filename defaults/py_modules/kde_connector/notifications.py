import json
import asyncio

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError, ClientOSError

import decky_plugin


BASE_URL = "http://localhost:8080"
SHARED_CONTEXT_TITLE = "SharedJSContext"


class NotificationClient:
    client = None
    websocket = None

    async def configure(self):
        if self.client is None:
            self.client = ClientSession()

        ws_url = None
        while True:
            try:
                res = await self.client.get(f"{BASE_URL}/json")
            except ClientConnectorError:
                await asyncio.sleep(5)
                continue
            except ClientOSError:
                await asyncio.sleep(1)
                continue
            except TimeoutError:
                await asyncio.sleep(1)
                continue

            tabs = await res.json()
            for tab in tabs:
                if tab["title"] == SHARED_CONTEXT_TITLE:
                    ws_url = tab["webSocketDebuggerUrl"]
                    break

            if ws_url is None:
                asyncio.sleep(5)
            else:
                break

        decky_plugin.logger.info(f"Found websocket URL: {ws_url}")

        if self.websocket is None:
            self.websocket = await self.client.ws_connect(ws_url)

    async def shutdown(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        if self.client:
            await self.client.close()
            self.client = None

    async def _send(self, exp):
        decky_plugin.logger.info(f"Sending to frontend: {exp}")
        await self.websocket.send_json({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": exp,
                "userGesture": True,
                "awaitPromise": False
            } 
        })

    async def sendPairingRequest(self, device):
        exp = f"DeckyPluginNotificationsSharedMethods.SendPairNotificationRequest({json.dumps(device)})"
        await self._send(exp)

    async def send_notification(self, title, body, icon = None):
        data = {
            "title": title,
            "body": body,
        }
        if icon:
            data["icon"] = icon
            
        exp = f"DeckyPluginNotificationsSharedMethods.SendNotification({json.dumps(data)})"
        await self._send(exp)

    async def push(self, title, body):
        toast_data = {
            "title": title,
            "body": body
        }

        exp = f"toast_data = {json.dumps(toast_data)};"

        """
        if "icon" in json_data:
            args = {
                "src": json_data["icon"],
                "style": {
                    "height": "100%"
                }
            }
            icon_create = (
                f"icon = window.react_create_element('img', {json.dumps(args)});"
            )
            exp += f"{icon_create}; toast_data['icon'] = icon;"

        if "picture" in json_data:
            args = {
                "src": json_data["picture"],
                "style": {
                    "height": "90%"
                }
            }
            img_create = f"picture = window.react_create_element('img', {json.dumps(args)})"
            exp += f"{img_create}; toast_data['logo'] = picture;"
        """

        exp += f"window.DeckyPluginLoader.toaster.toast(toast_data)"
        decky_plugin.logger.info(f"Current expression: {exp}")

        await self._send(exp)


notification_client = NotificationClient()

