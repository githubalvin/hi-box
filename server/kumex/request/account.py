from const import REQUSET_GET
from . import Request


class AccountRequest(Request):

    METHOD = REQUSET_GET
    ENDPOINT = "/api/v1/account-overview"

    async def get_account_info(self, currency):
        return (await self.get(self.get_url("?currency=%s" % currency)))
