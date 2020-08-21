

class DecisionBase:

    PENDING = 1
    IDLE = 2

    def __init__(self):
        self.state = IDLE

    async def setup(self):
        """初始化"""

    async def analysis(self):
        """分析"""

    async def decision(self):
        """决策"""