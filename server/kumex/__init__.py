import aiohttp
import base64
import hashlib
import hmac
import time
import json
import logging

from uuid import uuid1
from urllib.parse import urljoin

from driver.exchange import ExchangeAbstract

from .const import (PUB_MSG_HELLO,
                    PUB_MSG_ACK,
                    PUB_MSG_ERR,
                    PUB_MSG_PING,
                    PUB_MSG_PONG,
                    PUB_MSG_SUB,
                    PUB_MSG_UNSUB)
from .request import MarketRequest
from .request import TradeDataRequest
from .request import UserRequest
from .request import WebsocketRequest


mixin = [MarketRequest, TradeDataRequest,
         UserRequest, WebsocketRequest]

_LOGGER = logging.getLogger("kumex")
_LOGGER.setLevel(logging.DEBUG)


class KuMexExchange(ExchangeAbstract, *mixin):
    """ KuMex
    """
    def __init__(self, url, key, secret, passphrase, private=False):
        super(KuMexExchange, self).__init__(url)
        self.api_key = key
        self.api_secret = secret
        self.api_passphrase = passphrase
        self.private = private
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
        try:
            msg_content = json.loads(msg_data)
        except Exception:
            return None, None, None

        msg_type = msg_content.get('type', None)
        msg_topic = None
        if msg_type == PUB_MSG_HELLO:
            pass
        elif msg_type == PUB_MSG_ACK:
            msg_id = msg_content["id"]
            msg_topic = self.idtotopic.pop(msg_id, None)
        elif msg_type == PUB_MSG_PONG:
            pass
        elif msg_type == PUB_MSG_ERR:
            _LOGGER.error(msg_content['data'])
        elif msg_type is not None:
            msg_topic = msg_content["topic"]
        return msg_type, msg_topic, msg_content

    async def _keepalive(self):
        msg = {
            'id': str(int(time.time() * 1000)),
            'type': PUB_MSG_PING
        }
        await self.websocket.send_json(msg)

    async def _sub_request(self, topic):
        id = str(int(time.time() * 1000))
        msg = {
            'id': id,
            'type': PUB_MSG_SUB,
            'topic': topic,
            'privateChannel': self.private,
            'response': True
        }
        self.idtotopic[id] = topic
        await self.websocket.send_json(msg)

    async def _unsub_request(self, topic):
        id = str(int(time.time() * 1000))
        msg = {
            'id': id,
            'type': PUB_MSG_UNSUB,
            'topic': topic,
            'privateChannel': self.private,
            'response': True
        }
        self.idtotopic[id] = topic
        await self.websocket.send_json(msg)
