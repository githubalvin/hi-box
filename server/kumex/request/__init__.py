#pylint: disable-all

from utils import join_url, check_respond


class Request:

    METHOD = ""
    ENDPOINT = ""

    def get_url(self, *extra):
        return join_url(self.url, self.ENDPOINT, *extra)

    async def get(self, url):
        """HTTP GET"""
        header = self.request_header(self.METHOD + url)
        print(header)
        async with self.session.get(url, headers=header) as r:
            return (check_respond(await r.json()))

    async def post(self, url):
        """HTTP POST"""
        header = self.request_header(self.METHOD + url)
        async with self.session.post(url, headers=header) as r:
            return (check_respond(await r.json()))
