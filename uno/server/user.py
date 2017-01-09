# -*- coding: UTF-8 -*-
import json
import uuid
import asyncio
import random
import logging

from uno.game.deck import Card
from uno.game.ai import AILogic
from uno.server.event_manager import event_manager

logger = logging.getLogger(__name__)


class User(object):
    name = None
    uid = None
    round_uid = None
    protocol = None

    def __init__(self, name, protocol):
        self.uid = str(uuid.uuid4())
        self.name = name
        self.protocol = protocol

    def __str__(self):
        return "{0} - {1}".format(self.name, self.uid)


class HumanUser(User):
    pass


class AISocket(object):
    fn = None

    def __init__(self, fileno):
        self.fn = fileno

    def fileno(self):
        return self.fn


class AITransport(object):
    socket = None

    def __init__(self):
        self.socket = AISocket(str(uuid.uuid4()))

    def get_extra_info(self, info_name):
        return self.socket


class AIProtocol(object):
    user = None
    ai_logic = None

    def __init__(self, user):
        self.transport = AITransport()
        self.user = user
        self.ai_logic = AILogic(self)

    @asyncio.coroutine
    def send_message(self, data):
        logger.debug('ai received message %s', data)
        self.ai_logic.process_notification(data)


class AIUser(User):

    def __init__(self):
        self.name = "AI_{}".format(random.randint(1, 100))
        self.uid = str(uuid.uuid4())
        self.protocol = AIProtocol(self)
        self.cards = []
        self.ai_cards = list()
