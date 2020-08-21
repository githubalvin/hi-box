import asyncio
import logging

from tradecore import TradeController

_LOGGER = logging.getLogger("main")
_LOGGER.setLevel(logging.DEBUG)


async def _boostrap():
    _LOGGER.info("pandora boostrap...")

    logging.basicConfig(level=logging.DEBUG)

    await TradeController().setup()


async def main():

    await _boostrap()

    control = TradeController()

    while True:
        control.execute()
        await asyncio.sleep(0.1)

    await control.release()


if __name__ == '__main__':
    asyncio.run(main())