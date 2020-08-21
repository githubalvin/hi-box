import asyncio
import logging

from kumex import KuMexExchange
from utils import Singleton

_LOGGER = logging.getLogger("control")
_LOGGER.setLevel(logging.DEBUG)


class TradeController(Singleton):

    def __init__(self):
        self.exchanges = []
        self.strategies = []

    @property
    def kumex(self):
        return self.exchanges[0]

    async def setup(self):
        kumex = KuMexExchange('https://api-sandbox-futures.kucoin.com',
                              '5f3cf2295b13f000064986a6',
                              '8436b3ec-892b-4f2f-ae65-4a4fa3768cac',
                              '1234567')
        kumex.setup()
        self.exchanges.append(kumex)

        await kumex.ws_connect(*await kumex.get_ws_token())
        await kumex.sub_market_tiker('XBTUSDM', self.market_ticker)
        _LOGGER.debug("kumex setup suc")

        await self.load_all_strategies()
        _LOGGER.debug("strategies load suc")

    async def release(self):
        for obj in self.exchanges:
            await obj.release()

    async def load_all_strategies(self):
        """加载所有策略模型"""
        from .strategy.spot_contract import SpotContract

        sc = SpotContract()
        await sc.setup()
        self.strategies.append(sc)

    async def shut_strategies(self, model):
        """关闭策略模型"""

    def execute(self):
        """并发分析决策模型"""
        for dec in self.strategies:
            if dec.state == dec.PENDING:
                continue
            asyncio.ensure_future(dec.execute())

    def market_ticker(self, msg_type, data):
        """交易市场实时行情"""
        if msg_type == "ack":
            _LOGGER.info("subscribe market ticket suc")
            return

        symbol =  data["symbol"]
        sequece = data["sequence"]
        side = data["side"]
        price = data["price"]
        size = data["size"]
        traceid = data["tradeId"]
        bestbidsize = data["bestBidSize"]
        bestbidprice = data["bestBidPrice"]
        bestaskprice = data["bestAskPrice"]
        bestasksize = data["bestAskSize"]
        time = data["time"]
