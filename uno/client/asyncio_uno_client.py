# -*- coding: UTF-8 -*-
import sys
import json
import asyncio

from uno.protocol.service import uno_service
Card = uno_service.Card
NotificationType = uno_service.NotificationType
Command = uno_service.Command


class SubscriberClientProtocol(asyncio.Protocol):
    def __init__(self, loop, queue):
        self.transport = None
        self.loop = loop
        self._ready = asyncio.Event()
        self.queue = asyncio.Queue()
        protocol = self
        asyncio.Task(self._send_messages())  # Or asyncio.ensure_future if using 3.4.3+

    async def _send_messages(self):
        """ Send messages to the server as they become available. """
        await self._ready.wait()
        print("Ready!")
        while True:
            data = await self.queue.get()
            input_list = data.split(' ')
            username = None
            if input_list:
                command_text = input_list[0].strip()
                if command_text.upper() in uno_service.Command.items:
                    command_code = getattr(uno_service.Command, command_text.upper())
                    if command_code == uno_service.Command.LOGIN:
                        username = input_list[1].strip('')
                    if command_code == uno_service.Command.PUT:
                        if len(input_list) == 2:
                            card = uno_service.Card.fromstr(input_list[1].strip(''))
                        else:
                            card = None
                    else:
                        card = None
                    request = uno_service.UnoService.execute_command.request(
                        command_code,
                        username=username,
                        card=card
                    )
                    #print('Message sent: {!r}'.format(request))
                    self.transport.write(uno_service.dumps(request))
                else:
                    print('Command not found')

    def connection_made(self, transport):
        """ Upon connection send the message to the
        server

        A message has to have the following items:
            type:       subscribe/unsubscribe
            channel:    the name of the channel
        """
        self.transport = transport
        #print("Connection made.")
        self._ready.set()

    def data_received(self, data):
        """ After sending a message we expect a reply
        back from the server

        The return message consist of three fields:
            type:           subscribe/unsubscribe
            channel:        the name of the channel
            channel_count:  the amount of channels subscribed to
        """
        #print('data received')
        #print(data)
        while data:
            response = uno_service.loads(
                uno_service.UnoService.get_notification.response, data
            )
            # print(response)
            if response.success:
                allowed_actions = ''
                if response.success.allowed_actions:
                    allowed_actions = 'allowed actions: {}'.format(
                        [Command.name_of(item) for item in response.success.allowed_actions]
                    )
                print(
                    NotificationType.name_of(response.success.type),
                    Card.simple_str(response.success.card),
                    allowed_actions
                )
                if response.success.message:
                    for item in response.success.message.split(';'):
                        print(item)
            else:
                print(response)
            data = data[len(uno_service.dumps(response)):]

    def connection_lost(self, exc):
        print('The server closed the connection')
        print('Stop the event loop')
        self.loop.stop()


messages = ['login sdf', 'start']

async def aio_readline(protocol):
    while messages:
        mes = messages.pop(0)
        await protocol.queue.put(mes)
        await asyncio.sleep(1)

    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        await protocol.queue.put(line)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    coro = loop.create_connection(
        lambda: SubscriberClientProtocol(loop, queue), '127.0.0.1', 8888
    )
    _, proto = loop.run_until_complete(coro)
    asyncio.async(aio_readline(proto))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Closing connection')
    loop.close()
