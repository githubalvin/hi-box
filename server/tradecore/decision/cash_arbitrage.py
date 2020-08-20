"""期现套利策略"""
from .. import TradeController
from .base import DecisionBase


class CashArbitrage(DecisionBase):

    async def setup(self):
        """初始化"""
        print("cash arbitrage setup")
        kumex = TradeController().kumex
        bt = await kumex.get_account_overview('XBT')
        print("xbt overview: ", bt)

    async def analysis(self):
        """分析"""

    async def decision(self):
        """决策"""