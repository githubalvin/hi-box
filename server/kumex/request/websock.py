# pylint: disable=all


class WebsocketRequest:

    async def subscribe(self, topic, handle):
        """ Websocket subscibe

        Args:
            topic: subscribe what
            handle: publish callback
        """
        msg = {
            'id': str(int(time.time() * 1000)),
            'type': 'subscribe',
            'topic': topic,
            'privateChannel': self.private,
            'response': True
        }
        self.publish_handler[topic] = handle
        await self.websocket.send_json(msg)

    async def unsubscribe(self, topic):
        """ Websocket unsubscibe

        Args:
            topic: unsubscribe what
        """
        msg = {
            'id': str(int(time.time() * 1000)),
            'type': 'unsubscribe',
            'topic': topic,
            'privateChannel': self.private,
            'response': True
        }
        if topic in self.publish_handler:
            del self.publish_handler[topic]
        await self.websocket.send_json(msg)