import asyncio


class StrategyBase:
    """"策略模型"""

    PENDING = 1
    IDLE = 2

    def __init__(self):
        self.state = self.IDLE

    async def setup(self):
        """初始化"""

    async def execute(self):
        """执行策略"""
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

    async def decision(self):
        """决策"""
        raise NotImplementedError

    async def handle_exception(self, e):
        """"异常处理
        
        当策略出现异常的情况，可以做一些必要的风险管控措施
        """
        raise