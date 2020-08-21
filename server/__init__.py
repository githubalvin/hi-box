import asyncio
import logging

from console import LocalConsole
from tradecore import TradeController

_LOGGER = logging.getLogger("main")
_LOGGER.setLevel(logging.DEBUG)


async def _boostrap():
    _LOGGER.info("pandora boostrap...")

    logging.basicConfig(level=logging.DEBUG)

    await TradeController().setup()


async def main_loop():

    await _boostrap()

    control = TradeController()

    while True:
        control.analysis()
        await asyncio.sleep(0.01)

    await control.release()


async def main():
    console = LocalConsole()

    await asyncio.gather(
        main_loop(),
        console.loop(),
    )


if __name__ == '__main__':
    asyncio.run(main())