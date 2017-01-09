# -*- coding: UTF-8 -*-
import asyncio
import logging

import uvloop

from uno.server.event_manager import event_manager
from uno.server.game_queue import game_queue
from uno.server.login_manager import login_manager
from uno.server.online_players import online_players

from uno.protocol.service import uno_service


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
logging.basicConfig(format='%(levelname)s:%(module)s:\t%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

asyncio.Task(event_manager.process_events())
asyncio.Task(game_queue.process_tick())


class UnoServerProtocol(asyncio.Protocol):

    def __init__(self, *args, **kwargs):
        super(UnoServerProtocol, self).__init__(*args, **kwargs)
        self._ready = asyncio.Event()
        self.queue = asyncio.Queue()
        asyncio.async(self._send_messages())  # Or asyncio.ensure_future if using 3.4.3+

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.debug('Connection from {}'.format(peername))
        self.transport = transport
        self.send_message(
            uno_service.Notification(uno_service.NotificationType.CONNECTED)
        )
        self._ready.set()

    def connection_lost(self, exc):
        event_manager.add_event({
            'channel': 'data_received',
            'code': 'user_disconnected',
            'protocol': self
        })

    @asyncio.coroutine
    def _send_messages(self):
        """ Send messages to the server as they become available. """
        yield from self._ready.wait()
        print("Ready!")
        while True:
            data = yield from self.queue.get()
            if not self.transport.is_closing():
                self.transport.write(data)

    @asyncio.coroutine
    def send_message(self, data):
        """ Feed a message to the sender coroutine. """
        yield from self.queue.put(uno_service.dumps(data))

    def data_received(self, data):
        request = uno_service.loads(uno_service.UnoService.execute_command.request, data)
        try:
            message = data.decode()
        except:
            message = None
        if message is None or not message.strip():
            self.transport.write('incorrect data\n'.encode())
            logger.debug('incorrect data')
        else:
            event_manager.add_event({
                'channel': 'data_received',
                'code': 'data_received',
                'data': request,
                'protocol': self
            })
            logger.debug('Data received: {!r}'.format(message))

loop = asyncio.get_event_loop()

# Each client connection will create a new protocol instance
coro = loop.create_server(UnoServerProtocol, '127.0.0.1', 8888)
server = loop.run_until_complete(coro)
# server = loop.run_until_complete(record_user_score('tata', 55))

# Serve requests until Ctrl+C is pressed
logger.info('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
