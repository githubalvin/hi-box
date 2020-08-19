import asyncio
import logging

from console import LocalConsole
from tradecore.machine import Machine

_LOGGER = logging.getLogger("main")


def _boostrap():
    """启动引导"""
    _LOGGER.info("pandora boostrap...")

    Machine().setup()


async def main_loop():

    _boostrap()

    machine = Machine()
    
    print(await machine.kumex.get_account_info("XBT"))

    while True:
        try:
            await machine.analysis()
        except Exception:
            pass
        await asyncio.sleep(1)


async def main():
    console = LocalConsole()

    await asyncio.gather(
        main_loop(),
        console.loop(),
    )


if __name__ == '__main__':
    asyncio.run(main())