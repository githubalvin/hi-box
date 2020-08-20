import aiohttp
import asyncio
import base64
import hashlib
import hmac
import time
import json

from uuid import uuid1
from urllib.parse import urljoin

from .request.market_data import MarketDataRequest
from .request.token import TokenRequest
from .request.trade import TradeDataRequest
from .request.user import UserRequest
from .request.websock import WebsocketRequest


mixin = [MarketDataRequest, TokenRequest, TradeDataRequest,
         UserRequest, WebsocketRequest]


class KuMexExchange(*mixin):
    """ KuMex Driver
    """
    def __init__(self, url, key, secret, passphrase, private=False):
        self.url = url
        self.request = None
        self.api_key = key
        self.api_secret = secret
        self.api_passphrase = passphrase
        self.private = private
        self.websocket = None
        self.publish_handler = {}

    @staticmethod
    async def _check_response_data(response_data):
        if response_data.status == 200:
            try:
                data = await response_data.json()
            except aiohttp.ContentTypeError:
                raise
            if data and 'code' in data:
                if data.get('code') == '200000':
                    if data.get('data'):
                        return data['data']
                    else:
                        return data
                else:
                    raise Exception("{}-{}".format(response_data.status, await response_data.text()))
        else:
            raise Exception("{}-{}".format(response_data.status, await response_data.text()))

    def setup(self):
        self.request = aiohttp.ClientSession()

    async def release(self):
        if self.request:
            await self.request.close()
            self.request = None

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def _request(self, method, uri, timeout=30, auth=True, params=None) -> dict:
        uri_path = uri
        data_json = ''

        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json += '&'.join(strl)
                uri += '?' + data_json
                uri_path = uri
        else:
            if params:
                data_json= json.dumps(params)
                uri_path = uri + data_json

        headers = {}
        if auth:
            now_time = int(time.time()) * 1000
            str_to_sign = str(now_time) + method + uri_path
            sign = base64.b64encode(
                hmac.new(self.api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
            headers = {
                "KC-API-SIGN": sign.decode('utf-8'),
                "KC-API-TIMESTAMP": str(now_time),
                "KC-API-KEY": self.api_key,
                "KC-API-PASSPHRASE": self.api_passphrase,
                "Content-Type": "application/json"
            }

        url = urljoin(self.url, uri)

        kwargs = {
            "timeout": timeout,
            "headers": headers,
            }

        if method not in ['GET', 'DELETE']:
            kwargs["data"] = data_json

        async with self.request.request(method, url, **kwargs) as r:
            return (await self._check_response_data(r))

    async def _connect(self, url, ping_timeout, encryt, max_reconnect, retry_interval, waiter):
        assert self.websocket is None, "websocket already exists!"

        _reconnect = max_reconnect

        def _awake_waiter():
            if waiter and not waiter.done():
                waiter.set_result(None)
                waiter = None

        while True:
            if _reconnect < 0:
                _awake_waiter()
                break

            async with self.request.ws_connect(url, ssl=encryt) as ws:
                _awake_waiter()
                self.websocket = ws
                _last_ping = time.time()

                async for msg in ws:
                    msg_data = None
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            msg_data = json.loads(msg.data)
                        except Exception:
                            pass
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSE:
                        break

                    if msg_data:
                        topic = msg_data["topic"]
                        if topic in self.publish_handler:
                            try:
                                await self.publish_handler[topic](msg_data)
                            except Exception:
                                pass

                    now = time.time()
                    interval = now - _last_ping
                    _last_ping = now

                    if interval > ping_timeout:
                        await self.keepalive()
        
            # reset websocket and try reconnect
            self.websocket = None
            _reconnect -= 1
            await asyncio.sleep(retry_interval)

    async def ws_connect(self, url:str, encryt:bool, ping_timeout:int,
                   max_reconnect=10, retry_interval=5):
        """Websocket connect"""
        loop = asyncio.get_event_loop()
        waiter = loop.create_future()
        asyncio.ensure_future(
            self._connect(url, ping_timeout, encryt, max_reconnect, retry_interval, waiter))
        await waiter

    async def keepalive(self):
        msg = {
            'id': str(int(time.time() * 1000)),
            'type': 'ping'
        }
        await self.websocket.send_json(msg)



