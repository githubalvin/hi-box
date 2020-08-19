from const import REQUSET_POST
from . import Request


class WebSocketPubTokenRequest(Request):

    METHOD = REQUSET_POST
    ENDPOINT = "/api/v1/bullet-public"

    async def get_public_token(self):
        data = await self.post(self.get_url())
        token = data["token"]
        connect = data["instanceServers"]
        return token, connect

        
