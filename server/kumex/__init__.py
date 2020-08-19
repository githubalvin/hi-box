import base64
import hashlib
import hmac

from utils import utctimestamp
from exchange.base import ExchangeAbstract

from .request.account import AccountRequest
from .request.time import TimeRequest

mixin = [AccountRequest, TimeRequest]


class KuMexExchange(ExchangeAbstract, *mixin):

    def __init__(self, url, key, secret, passphrase):
        super(KuMexExchange, self).__init__(url)
        self.api_key = key
        self.api_secret = secret
        self.api_passphrase = passphrase

    def _encode_sign(self, secret, timestamp, sign):
        """生成消息签名"""
        sign = timestamp + sign
        return base64.b64encode(
            hmac.new(secret.encode('utf-8'), sign.encode('utf-8'), hashlib.sha256).digest()).decode('utf8')

    def request_header(self, sign):
        """生成请求头"""
        timestamp = str(utctimestamp() * 1000)
        return {
            "KC-API-SIGN": self._encode_sign(self.api_secret, timestamp, sign),
            "KC-API-TIMESTAMP": str(timestamp),
            "KC-API-KEY": self.api_key,
            "KC-API-PASSPHRASE": self.api_passphrase,
        }