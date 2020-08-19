import aiohttp
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


mixin = [MarketDataRequest, TokenRequest, TradeDataRequest, UserRequest,]


class KuMexExchange(*mixin):
    """ KuMex Driver
    """
    def __init__(self, url, key, secret, passphrase):
        self.url = url
        self.request = None
        self.api_key = key
        self.api_secret = secret
        self.api_passphrase = passphrase

    @staticmethod
    async def _check_response_data(response_data):
        if response_data.status == 200:
            try:
                data = await response_data.json()
            except ValueError:
                raise
            else:
                if data and data.get('code'):
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
                "KC-API-SIGN": str(sign),
                "KC-API-TIMESTAMP": str(now_time),
                "KC-API-KEY": self.api_key,
                "KC-API-PASSPHRASE": self.api_passphrase,
                "Content-Type": "application/json"
            }
        url = urljoin(self.url, uri)
        kwargs = {
            "headers": headers,
            "timeout": timeout,
        }

        if method not in ['GET', 'DELETE']:
            kwargs["data"] = data_json
 
        async with self.request.request(method, url, **kwargs) as r:
            return (await self._check_response_data(r))

    async def subscribe(self, url):
        """Subscribe
        
        Via Websocket connect to server, subscribe channels
        """
        async with self.request.ws_connect(url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == 'close cmd':
                        await ws.close()
                        break
                    else:
                        await ws.send_str(msg.data + '/answer')
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break