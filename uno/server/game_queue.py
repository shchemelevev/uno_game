# -*- coding: UTF-8 -*-
import asyncio
import logging
from datetime import datetime

from uno.server.event_manager import event_manager
from uno.game.uno_round import UnoRound
from uno.server.user import AIUser
from uno.server.online_users import online_users

from uno.protocol.service import uno_service
NotificationType = uno_service.NotificationType

logger = logging.getLogger(__name__)


class GameQueue(object):
    players_list = []

    def __init__(self):
        self.players_list = list()

    def _get_max_time_delta(self, current_time):
        max_delta = 0
        for data in self.players_list:
            player, start_time = data
            delta = current_time - start_time
            max_delta = max(delta.seconds, max_delta)
        return max_delta

    def check_start_conditions(self):
        # Игра начинается, когда наступает одно из событий:
        #   - В очереди десять игроков.
        #   - Самый "старый" игрок ждет более 1-й минуты и в очереди больше одного игрока.
        #   - Самый "старый" игрок ждет более 2-х минут.

        if len(self.players_list) == 10:
            return True

        if len(self.players_list) >= 1 and self._get_max_time_delta(datetime.now()) > 10:
            return True

        if self._get_max_time_delta(datetime.now()) > 20:
            return True

        return False

    def start_game(self):
        logger.debug('starting new game')
        uno_round = UnoRound()
        event_manager.subscribe('game_command', uno_round)
        for data in self.players_list:
            player_uid, time = data
            uno_round.add_player(player_uid, 'human')

        if len(self.players_list) < 2:
            for item in range(1):
                ai_user = AIUser()
                online_players.add_player(ai_user, ai_user.protocol)
                uno_round.add_player(ai_user.uid)

        uno_round.start_round()
        self.players_list = list()
        logger.debug('game started')

    async def finish_game(self, event):
        logger.debug('finishing game')
        uno_round = event['uno_round']
        event_manager.unsubscribe('game_command', uno_round)

    def add_player(self, player_uid, time):
        self.players_list.append((player_uid, time))
        if self.check_start_conditions():
            self.start_game()

    async def process_tick(self):
        while True:
            if len(self.players_list) >= 1:
                if self.check_start_conditions():
                    self.start_game()
            await asyncio.sleep(1)

    async def process_event(self, event):
        if event['code'] == 'game_start_request':
            self.add_player(event['player_uid'], datetime.now())
            logger.debug('player %s added to queue', event['player_uid'])

        if event['code'] == 'finish_game':
            await self.finish_game(event)

game_queue = GameQueue()
event_manager.subscribe('game_queue', game_queue)
