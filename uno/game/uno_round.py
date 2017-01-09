# -*- coding: UTF-8 -*-
import random
import uuid
import logging

from uno.game.deck import Deck, IncorrectCardError
from uno.game.actions import allowed_actions_for_card
from uno.game.player import Player

from uno.server.event_manager import event_manager

from uno.protocol.service import uno_service
NotificationType = uno_service.NotificationType
Command = uno_service.Command

logger = logging.getLogger(__name__)
LEFT = 1
RIGHT = -1
MAX_PLAYERS = 10


class ActionNotAllowedError(Exception):
    pass


class NotYourTurnException(Exception):
    pass


class MaxPlayersReachedException(Exception):
    pass


class UnoRound(object):

    uid = None
    direction = LEFT
    deck = None
    player_list = None
    current_player_index = None
    actions_list = None
    player_by_uid = None
    taken_card = None
    human_players = None

    def __init__(self, deck=None):
        self.player_list = list()
        self.uid = str(uuid.uuid4())
        self.player_by_uid = dict()
        self.human_players = list()
        if deck is None:
            self.deck = Deck()
        else:
            self.deck = deck

    def get_player(self, player_uid):
        return self.player_by_uid[player_uid]

    def add_player(self, player_uid, player_type=None):
        if player_type == 'human':
            self.human_players.append(player_uid)
        if len(self.player_list) < MAX_PLAYERS:
            player = Player(player_uid)
            self.player_list.append(player)
            self.player_by_uid[player_uid] = player
            return player
        else:
            raise MaxPlayersReachedException('Max players reached')

    def set_dealer(self):
        self.current_player_index = random.randint(0, len(self.player_list)-1)

    def deal_cards(self, deck, player_list):
        CARDS_TO_DEAL = 7
        for item in range(CARDS_TO_DEAL):
            for player in player_list:
                card = deck.get_card()
                player.add_card(card)

    def get_allowed_actions(self):
        return set([item.command_id for item in self.actions_list])

    def set_first_card(self):
        card = self.deck.get_card()
        while card.action is not None:
            self.deck._cards.append(card)
            card = self.deck.get_card()
        self.deck.put_card(card)
        self.actions_list = allowed_actions_for_card(card)

    def notify_all(self, **kwargs):
        for player in self.player_list:
            player.notify_user(**kwargs)

    def notify_all_except_current(self, **kwargs):
        for player in self.player_list:
            if player != self.current_player:
                player.notify_user(**kwargs)

    def start_round(self):
        self.deal_cards(self.deck, self.player_list)
        self.set_dealer()
        self.set_first_card()

        self.notify_all(code=NotificationType.ACTIVE_CARD, card=self.deck.active_card)
        self.notify_all(code=NotificationType.ROUND_STARTED, round_uid=self.uid)
        self.current_player.notify_user(
            code=NotificationType.YOUR_TURN,
            allowed_actions=self.get_allowed_actions()
        )
        logger.debug('round started')

    @property
    def current_player(self):
        return self.player_list[self.current_player_index]

    def get_score(self):
        total = 0
        for player in self.player_list:
            for card in player.cards:
                total += card.cost
        return total

    def change_direction(self):
        if self.direction == RIGHT:
            self.direction = LEFT
        else:
            self.direction = RIGHT

    def remove_player(self, player_uid):
        player = self.player_by_uid[player_uid]
        current_player = self.current_player
        if player_uid == self.current_player.uid:
            if len(self.human_players) > 0:
                self.set_next_player()
                self.current_player.notify_user(
                    code=NotificationType.YOUR_TURN,
                    allowed_actions=self.get_allowed_actions()
                )
        self.current_player_index = self.player_list.index(current_player)
        self.human_players.remove(player_uid)
        self.player_by_uid.pop(player_uid)
        self.player_list.remove(player)
        self.notify_all(code=NotificationType.PLAYER_DISCONNECTED)
        self.check_for_win()

    def set_next_player(self):
        if self.direction == 1 and self.current_player_index + 1 >= len(self.player_list):
            self.current_player_index = 0
        elif self.direction == -1 and self.current_player_index - 1 < 0:
            self.current_player_index = len(self.player_list) - 1
        else:
            self.current_player_index += self.direction

    def process_input(self, player, command_request):
        if player != self.current_player:
            raise NotYourTurnException('not your turn')

        # TODO: check player has card

        action_processed = False
        for action in self.actions_list:
            if action.check_condition(command_request, self):
                action.update_round(command_request, self)
                action_processed = True
                break

        if not action_processed:
            raise ActionNotAllowedError('action_not_allowed')
        else:
            self.check_for_win()

    async def process_event(self, event):
        if event['channel'] == 'game_command':
            if event['player_uid'] in self.player_by_uid.keys():
                if event.get('command') == Command.DISCONNECT:
                    self.remove_player(event['player_uid'])
                    return True
                try:
                    self.process_input(
                        self.get_player(event['player_uid']), event['command']
                    )
                except NotYourTurnException:
                    self.get_player(event['player_uid']).notify_user(
                        exception=True,
                        not_your_turn=uno_service.NotYourTurn()
                    )
                except ActionNotAllowedError:
                    self.get_player(event['player_uid']).notify_user(
                        exception=True,
                        not_allowed=uno_service.ActionNotAllowed(
                            'allowed actions : {}'.format(
                                set(
                                    [Command.name_of(item.command_id) for item in self.actions_list]
                                )
                            )
                        )
                    )

    def check_for_win(self):
        if len(self.human_players) == 0:
            event_manager.add_event(
                {'channel': 'game_queue', 'code': 'finish_game', 'uno_round': self}
            )
            return True
        if len(self.human_players) == 1 and len(self.player_list) == 1:
            self.notify_all(
                code=NotificationType.ROUND_FINISHED, winner=self.player_list[0].uid,
                uno_round=self
            )
            event_manager.add_event(
                {'channel': 'game_queue', 'code': 'finish_game', 'uno_round': self}
            )
        for player in self.player_list:
            if not player.cards:
                self.notify_all(
                    code=NotificationType.ROUND_FINISHED, winner=player.uid,
                    uno_round=self
                )
                event_manager.add_event(
                    {'channel': 'game_queue', 'code': 'finish_game', 'uno_round': self}
                )
                return True
        return False
