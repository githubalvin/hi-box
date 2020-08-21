import asyncio

from const import EXCHANGE_KUMEX
from kumex import KuMexExchange


class StrategyBase:
    """"策略模型"""

    PENDING = 1
    IDLE = 2
    CLOSE = 3

    def __init__(self):
        self.state = self.IDLE
        self.exchanges = []

    async def setup(self, config=None):
        """初始化"""
        for exchange in config:
            name = exchange['name']
            if name == EXCHANGE_KUMEX:
                kumex = KuMexExchange(exchange['url'],
                                      exchange['key'],
                                      exchange['secret'],
                                      exchange['passphrase'])
                kumex.setup()
                self.exchanges.append(kumex)
                await kumex.ws_connect(*await kumex.get_ws_token())

    async def init(self):
        """初始化"""

    async def close(self):
        """关闭策略"""
        for obj in self.exchanges:
            await obj.release()

    async def execute(self):
        """执行策略"""
        assert self.state == self.IDLE, "strategt executing"

        self.state = self.PENDING
        try:
            await self.analysis()
        except Exception as e:
            return await self.handle_exception(e)
        # Stop execution when exception occurs
        self.state = self.IDLE

    async def analysis(self):
        """分析"""
        raise NotImplementedError

    async def handle_exception(self, e):
        """"异常处理
        
        当策略出现异常的情况，可以做一些必要的风险管控措施
        """
        raise e
    
    def snapshot(self):
        """决策快照
        
        决策时，通过快照保留决策现场，方便复盘
        """