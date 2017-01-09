# -*- coding: UTF-8 -*-
import asyncio
import logging
from collections import defaultdict
from asyncio import Queue

logger = logging.getLogger(__name__)


class EventManager(object):
    event_queue = None
    _subscribers = None

    def __init__(self):
        self.event_queue = Queue()
        self._subscribers = defaultdict(set)

    def subscribe(self, event_type, subscriber):
        logger.debug('subscribe %s for %s', subscriber, event_type)
        self._subscribers[event_type].add(subscriber)

    def unsubscribe(self, event_type, subscriber):
        #TODO: wtf? where is the code?!
        try:
            self._subscribers[event_type].remove(subscriber)
        except ValueError:
            pass

    def add_event(self, event):
        logger.debug('put event %s into queue', event)
        self.event_queue.put_nowait(event)  # TODO: WTF? NOWAIT?

    async def process_events(self):
        while True:
            # logger.debug('Processing %s events', self.event_queue.qsize())
            while not self.event_queue.empty():
                event = await self.event_queue.get()
                logger.debug('processing event %s', event)
                subscribers_list = self._subscribers.get(event['channel'], [])
                for subscriber in subscribers_list:
                    await subscriber.process_event(event)
                if not subscribers_list:
                    logger.debug('no listeners for event %s', event)
            await asyncio.sleep(0.1)

event_manager = EventManager()
