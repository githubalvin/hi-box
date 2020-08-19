import asyncio
import logging

from console import LocalConsole
from tradecore import Machine, TradeController

_LOGGER = logging.getLogger("main")


def _boostrap():
    _LOGGER.info("pandora boostrap...")

    TradeController().setup()


async def main_loop():

    _boostrap()

    machine = Machine()
    control = TradeController()
    
    try:
        print(await control.kumex.get_account_overview())
    except Exception:
        raise
    finally:
        await control.release()

    while True:
        try:
            await machine.analysis()
        except Exception:
            pass
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