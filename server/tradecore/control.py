import asyncio
import logging
import json

from const import SPOT_CONTRACT
from utils import Singleton

_LOGGER = logging.getLogger("control")
_LOGGER.setLevel(logging.DEBUG)


class TradeController(Singleton):

    def __init__(self):
        self.strategies = []

    async def setup(self):
        config = {}
        with open("config.json", 'r') as f:
            config = json.loads(f.read())

        for detail in config["strategy"]:
            name = detail['name']

            if name == SPOT_CONTRACT:
                from strategy.spot_contract import SpotContract
                sc = SpotContract()
                await sc.setup(detail['exchange'])
                await sc.init()
                self.strategies.append(sc)

        _LOGGER.debug("strategies load suc")

    async def release(self):
        await self.shut_strategies()

    async def shut_strategies(self):
        """关闭策略"""
        for dec in self.strategies:
            if dec.state == dec.CLOSE:
                continue
            await dec.close()
        self.strategies= []

    def execute(self):
        """并发分析决策模型"""
        for dec in self.strategies:
            if dec.state == dec.PENDING:
                continue
            asyncio.ensure_future(dec.execute())
