import aiohttp
import asyncio
import base64
import hashlib
import hmac
import time
import json
import logging

from uuid import uuid1
from urllib.parse import urljoin
from const import (PUB_MSG_HELLO,
                   PUB_MSG_ACK,
                   PUB_MSG_ERR,
                   PUB_MSG_PING,
                   PUB_MSG_PONG,
                   PUB_MSG_SUB,
                   PUB_MSG_UNSUB)

from .request.market_data import MarketDataRequest
from .request.trade import TradeDataRequest
from .request.user import UserRequest
from .request.websock import WebsocketRequest


mixin = [MarketDataRequest, TradeDataRequest,
         UserRequest, WebsocketRequest]

_LOGGER = logging.getLogger("kumex")
_LOGGER.setLevel(logging.DEBUG)


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
        self.idtotopic = {}

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

    def _check_publish_data(self, msg_data):
        msg_type = msg_data.get('type', None)
        msg_topic = None
        if msg_type == PUB_MSG_HELLO:
            pass
        elif msg_type == PUB_MSG_ACK:
            msg_id = msg_data["id"]
            msg_topic = self.idtotopic.pop(msg_id, None)
        elif msg_type == PUB_MSG_PONG:
            pass
        elif msg_type == PUB_MSG_ERR:
            _LOGGER.error(msg_data['data'])
            pass
        elif msg_type is not None:
            msg_topic = msg_data["topic"]
        return msg_type, msg_topic, msg_data


    async def _connect(self, url, encryt, max_reconnect, retry_interval, waiter):
        assert self.websocket is None, "websocket already exists!"

        _reconnect = max_reconnect

        def _awake_waiter(waiter):
            if waiter and not waiter.done():
                waiter.set_result(None)
                waiter = None

        while True:
            if _reconnect < 0:
                _awake_waiter(waiter)
                break

            async with self.request.ws_connect(url, ssl=encryt) as ws:
                self.websocket = ws

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

                    msg_type, topic, data = self._check_publish_data(msg_data)
                    if msg_type == PUB_MSG_HELLO:
                        _awake_waiter(waiter)
                    elif topic and topic in self.publish_handler:
                        try:
                            self.publish_handler[topic](msg_type, data)
                        except Exception:
                            pass
        
            # reset websocket and try reconnect
            self.websocket = None
            _reconnect -= 1
            await asyncio.sleep(retry_interval)

    async def ws_connect(self, url:str, encryt:bool, ping_timeout:int,
                   max_reconnect=10, retry_interval=5):
        """Websocket connect
        
        Corutine will be blocked until websocket connected or try max_reconnect.
        Heartbeat keeps the whole life-cycle.

        Args:
            url:
            encryt:
            ping_timeout: heartbeat interval
            max_reconnect: reconnect cnt limit
            retry_interval:
        """
        loop = asyncio.get_event_loop()
        waiter = loop.create_future()
        asyncio.ensure_future(
            self._connect(url, encryt, max_reconnect, retry_interval, waiter))
        await waiter
        asyncio.ensure_future(self.heartbeat(ping_timeout))

    async def _keepalive(self):
        msg = {
            'id': str(int(time.time() * 1000)),
            'type': PUB_MSG_PING
        }
        await self.websocket.send_json(msg)

    async def heartbeat(self, interval):
        while True:
            if self.websocket:
                await self._keepalive()
            await asyncio.sleep(interval)

    async def subscribe(self, topic, handle):
        """ Websocket subscibe

        Args:
            topic: subscribe channel
            handle: publish callback

        Raises:
            ConnectionResetError: connect lost
        """
        id = str(int(time.time() * 1000))
        msg = {
            'id': id,
            'type': PUB_MSG_SUB,
            'topic': topic,
            'privateChannel': self.private,
            'response': True
        }
        self.idtotopic[id] = topic
        self.publish_handler[topic] = handle
        await self.websocket.send_json(msg)

    async def unsubscribe(self, topic):
        """ Websocket unsubscibe

        Args:
            topic: unsubscribe channel

        Raises:
            ConnectionResetError: connect lost
        """
        id = str(int(time.time() * 1000))
        msg = {
            'id': id,
            'type': PUB_MSG_UNSUB,
            'topic': topic,
            'privateChannel': self.private,
            'response': True
        }
        self.idtotopic[id] = topic
        if topic in self.publish_handler:
            del self.publish_handler[topic]
        await self.websocket.send_json(msg)



