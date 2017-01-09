# -*- coding: UTF-8 -*-
import logging

import score_storage
from event_manager import event_manager

logger = logging.getLogger(__name__)


class LoginManager(object):

    async def process_event(self, event):
        logging.debug('Login manager received event %s', event)
        if event.code == 'login':
            await self.login(event)
        elif event.code == 'logout':
            self.logout(event)

    async def login(self, event):
        score = await score_storage.get_user_score(event.data['username'])
        event_manager.add_event({
            'code': 'user_score_received',
            'username': event.data['username'],
            'score': score,
            'transport': event.data['transport']
        })

    def logout(self, event):
        logger.debug('Closing transport %s', event.data['transport'])
        event.data['transport'].close()

login_manager = LoginManager()
event_manager.subscribe('login', login_manager)
event_manager.subscribe('logout', login_manager)
