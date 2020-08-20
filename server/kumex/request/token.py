# pylint: disable=all
import time


class TokenRequest:

    async def get_ws_token(self, is_private=False):
        """
        https://docs.kumex.com/#apply-for-connection-token
        :param is_private private or public
        :return:
        """
        uri = '/api/v1/bullet-public'
        if is_private:
            uri = '/api/v1/bullet-private'

        ws_detail = await self._request('POST', uri, auth=is_private)
        ws_connect_id = str(int(time.time() * 1000))
        token = ws_detail['token']
        endpoint = ws_detail['instanceServers'][0]['endpoint']
        ws_endpoint = f"{endpoint}?token={token}&connectId={ws_connect_id}"
        if private:
            ws_endpoint += '&acceptUserMessage=true'
    
        ws_encrypt = ws_detail['instanceServers'][0]['encrypt']
        ws_timeout = int(ws_detail['instanceServers'][0]['pingTimeout'] / 1000) - 2

        return ws_endpoint, ws_encrypt, ws_timeout


