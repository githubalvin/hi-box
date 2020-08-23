"""期现套利策略

原理：
    由于交割期货合约本身的性质，最迟在合约到期的当天，它的价格必然会和现货价格相同。
    所以当期货合约和现货之间存在价差的时候，就可以进行无风险套利，套利机会多出现在市场波动率大的时候。

    基差=现货价格-期货价格

    当基差为负，且「基差绝对值>市价买卖手续费+滑点成本」时

    现货买进、期货做空（正向套利）

    基差缩小或者=0时，平仓

操作流程：
    步骤一

    实时监控基差，当发现期现货价差足够大时（百分比），即出现套利机会（具体这个价差多少我们后边单独讨论）

    步骤二

    在「币币交易」中使用USDT购买1BTC，此时在「币币账户」有1BTC

    步骤三

    进行资金划转，将1BTC划转到「交割/永续合约账户」，转到交割还是永续取决于你所观察的基差对是现货和什么合约对比，
    此时在「合约账户」有1BTC

    步骤四

    进行合约交易，做空BTC；做空的数量和划转到合约账户里的BTC数量一致

    ️使用全仓模式，杠杆选择10倍️（如果选择逐仓模式，一定要把自动追加保证金开启，保证做空数量和账户里币的数量一致，
    开10x、20x没啥影响），开仓后保险起见，可以检查合约持仓信息里面，预估强平价应该基本是0，也就是不会爆仓

    步骤五

    等待基差缩小，价差缩小到让我们满意的大小时，就是期现套利结束的时候，不一定非要等到合约交割日

    步骤六

    当期现货价差小于xx%时，可以考虑将合约平仓。在平仓之后我们「合约账户」获得的并不是USDT，而是BTC，
    还需要将这部分资金划转到「币币账户」，并将其卖出，换成USDT。

    这样就完成了一次期现套利，我们在「币币账户」的USDT增加了。


作者：袁嘉威
链接：https://www.jianshu.com/p/527172733e01
来源：简书
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
"""
import logging

from kumex.const import PUB_MSG_ACK
from .base import StrategyBase

_LOGGER = logging.getLogger("SC")


class SpotContract(StrategyBase):

    def __init__(self):
        super(SpotContract, self).__init__()
        self.cur_index_price = 0
        self.cur_mark_price = 0
        self.maker_feerate = 0
        self.taker_feerate = 0

    @property
    def kumex(self):
        return self.exchanges[0]

    async def init(self):
        self.instrument_handle = await self.kumex.sub_instrument(
            'XBTUSDM', self._instrument)

        data = await self.kumex.get_contract_detail('XBTUSDM')
        self.maker_rate = data["makerFeeRate"]
        _LOGGER.debug("contract detail: %s", data)

        _LOGGER.debug("overview btc: %s", await self.kumex.get_account_overview('XBT'))
        _LOGGER.debug("overview usdt: %s", await self.kumex.get_account_overview('USDT'))

    def _instrument(self, msg_type, data):
        _LOGGER.debug("instrument: %s", data)
        sub = data["subject"]
        if sub == "mark.index.price":   # 当前最新价格
            self.cur_index_price = data["data"]["indexPrice"]
            self.cur_mark_price = data["data"]["makrPrice"]
        elif sub == "funding.rate":     # 资金费率
            pass

    async def analysis(self):
        """分析市场实时行情"""
        _LOGGER.debug("analysis...")
        basic = self.cur_index_price - self.cur_mark_price
        if basic >= 0:  # 不做反向套利
            return
        ratio = abs(basic) / self.cur_mark_price
        if ratio <= self.taker_feerate:    # 成本控制
            return
        if ratio < 10:                  # 收益控制
            return        
        await self.kumex.create_limit_order(self, 'XBTUSDM', 'buy', 100, 1, self.cur_mark_price)
