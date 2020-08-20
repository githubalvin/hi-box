import asyncio
import logging

from kumex import KuMexExchange
from utils import Singleton

from .decision.cash_arbitrage import CashArbitrage

_LOGGER = logging.getLogger("control")
_LOGGER.setLevel(logging.DEBUG)


class TradeController(Singleton):

    def __init__(self):
        self.exchanges = []
        self.decisions = []

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

        await self.load_all_decision()
        _LOGGER.debug("decision load suc")

    async def release(self):
        for obj in self.exchanges:
            await obj.release()

    async def load_all_decision(self):
        """加载所有策略模型"""
        cash = cash_arbitrage.CashArbitrage()
        await cash.setup()
        self.decisions.append(cash)

    async def shut_decision(self, model):
        """关闭策略模型"""

    def analysis(self):
        """并发分析决策模型"""
        for dec in self.decisions:
            asyncio.ensure_future(dec.analysis())

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
