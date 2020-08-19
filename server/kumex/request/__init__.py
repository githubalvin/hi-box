#pylint: disable-all

from utils import join_url


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
            return (await r.json())
