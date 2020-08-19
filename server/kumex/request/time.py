from const import REQUSET_GET
from . import Request


class TimeRequest(Request):

    METHOD = REQUSET_GET
    ENDPOINT = "/api/v1/timestamp"

    async def get_server_timestamp(self):
        pass
        
