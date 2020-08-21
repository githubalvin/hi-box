import aiohttp
import asyncio


class SubscribeHandle:
    """订阅句柄"""

    def __init__(self):
        self.cancle = False

    def unsubscribe(self):
        self.cancle = True


class ExchangeAbstract:
    """ Exchange abstract driver
    """
    def __init__(self, url):
        self.url = url
        self.request = None
        self.websocket = None
        self.publish_handler = {}

    def setup(self):
        self.request = aiohttp.ClientSession()

    async def release(self):
        if self.request:
            await self.request.close()
            self.request = None

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def _connect(self, url, encryt, max_reconnect, retry_interval, waiter):
        assert self.websocket is None, "websocket already exists!"

        _reconnect = max_reconnect

        def _awake_waiter(waiter):
            if waiter and not waiter.done():
                waiter.set_result(None)
                waiter = None

        while True:
            if _reconnect < 0:
                _awake_waiter(waiter)
                break

            async with self.request.ws_connect(url, ssl=encryt) as ws:
                _awake_waiter(waiter)
                self.websocket = ws

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        msg_type, topic, content = self._check_publish_data(msg.data)

                        if topic and topic in self.publish_handler:
                            for handle, cb in self.publish_handler[topic][:]:
                                if handle.cancle:
                                    continue
                                self.publish_handler[topic].remove((handle, cb))
                                try:
                                    cb(msg_type, content)
                                except Exception:
                                    pass
                            # do unsubscrib when no subscriber
                            if not self.publish_handler[topic]:
                                try:
                                    await self._unsub_request(topic)
                                except Exception:
                                    continue
                                del self.publish_handler[topic]
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSE:
                        break
        
            # reset websocket and try reconnect
            self.websocket = None
            _reconnect -= 1
            await asyncio.sleep(retry_interval)

    async def ws_connect(self, url:str, encryt:bool, ping:int,
                         max_reconnect=10, retry_interval=5):
        """Websocket connect
        
        Corutine will be blocked until websocket connected or try max_reconnect.
        Heartbeat keeps the whole life-cycle.

        Args:
            url:
            encryt:
            ping: heartbeat interval
            max_reconnect: reconnect cnt limit
            retry_interval:
        """
        loop = asyncio.get_event_loop()
        waiter = loop.create_future()
        asyncio.ensure_future(
            self._connect(url, encryt, max_reconnect, retry_interval, waiter))
        await waiter
        asyncio.ensure_future(self.heartbeat(ping))

    async def heartbeat(self, interval):
        """Websockeet heartbeat
        
        Args:
            interval: ping interval
        """
        while True:
            if self.websocket:
                try:
                    await self._keepalive()
                except NotImplementedError:
                    break
            await asyncio.sleep(interval)

    async def subscribe(self, topic, cb):
        """ Websocket subscibe

        Args:
            topic: subscribe channel
            handle: publish callback

        Raises:
            ConnectionResetError: connect lost

        Returns:
            SubscribeHandle: which could be used to unsubscribe topic
        """
        handle = SubscribeHandle()
        if topic not in self.publish_handler:
            self.publish_handler[topic] = [(handle, cb)]
            try:
                await self._sub_request(topic)
            except Exception:
                del self.publish_handler[topic]
                raise
        else:
            self.publish_handler[topic].append((handle, cb))
        return handle

    def _check_publish_data(self, msg_data):
        """publish msg filter
        
        Args:
            msg_data: recieve binary

        Returns:
            msg_type, topic, content
        """
        raise NotImplementedError

    async def _keepalive(self):
        """keep websocket alive"""
        raise NotImplementedError

    async def _sub_request(self, topic):
        """Subscribe request

        Args:
            topic: subscribe channel
        """
        raise NotImplementedError

    async def _unsub_request(self, topic):
        """Unsubscribe request

        Args:
            topic: unsubscribe channel
        """
        raise NotImplementedError



