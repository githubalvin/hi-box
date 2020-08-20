import sys
import asyncio
import asyncio.tasks
import logging


_LOGGER = logging.getLogger("console")

class Console:

    def __init__(self):
        self.istream = None
        self.ostream = None
        self.input_bar = ">>"

    def parser_command(self, inpt):
        """"解析指令"""
        inpt = inpt.split(" ")
        cmd = inpt[0]
        args = inpt[1:]

    async def loop(self):
        while True:
            # self.parser_command(cmd)
            await asyncio.tasks.sleep(0.1)


class LocalConsole(Console):

     def __init__(self):
        super(LocalConsole, self).__init__()
        self.istream = sys.stdin
        self.ostream = sys.stdout
