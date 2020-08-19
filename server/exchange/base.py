import aiohttp


class ExchangeAbstract:
    """ 交易所抽象类
    """

    def __init__(self, url):
        self.url = url
        self.markets = {}
        self.session = None

    def setup(self):
        self.session = aiohttp.ClientSession()

    async def release(self):
        if self.session:
            await self.session.close()
            self.session = None


class MarketAbstract:
    """市场抽象类
    """
