# -*- coding: UTF-8 -*-
import json
import random
import logging

from uno.server.event_manager import event_manager
from uno.server.user import HumanUser

from uno.protocol.service import uno_service
NotificationType = uno_service.NotificationType
Card = uno_service.Card


logger = logging.getLogger(__name__)


class OnlinePlayers(object):
    uid = 'online_players_list'

    uid_protocol = dict()
    protocol_uid = dict()
    uid_player = dict()

    def __init__(self):
        self.uid_protocol = dict()
        self.protocol_uid = dict()
        self.uid_player = dict()

    def get_protocol_id(self, protocol):
        return id(protocol)
        # socket = protocol.transport.get_extra_info('socket')
        # return socket.fileno()

    def add_player(self, player, protocol):
        protocol_id = self.get_protocol_id(protocol)
        self.protocol_uid[protocol_id] = player.uid
        self.uid_protocol[player.uid] = protocol
        self.uid_player[player.uid] = player

    def remove_player(self, player, protocol):
        protocol_id = self.get_protocol_id(protocol)
        # TODO: fix bug
        # self.protocol_uid.pop(protocol_id)
        # self.uid_protocol.pop(player.uid)
        # self.uid_player.pop(player.uid)

    def get_player_by_protocol(self, protocol):
        return self.protocol_uid.get(
            self.get_protocol_id(protocol), None
        )

    def get_protocol_by_player_uid(self, player_uid):
        return self.uid_protocol.get(player_uid, None)

    def get_player_by_uid(self, player_uid):
        return self.uid_player[player_uid]

    async def process_event(self, event):
        # make processor
        if event['channel'] == 'data_received':
            request = event.get('data', '')
            if request:
                if request.command == uno_service.Command.LOGIN:
                    if self.get_player_by_protocol(event['protocol']) is None:
                        online_user = HumanUser(request.username, event['protocol'])
                        self.add_player(online_user, event['protocol'])
                if request.command == uno_service.Command.START:
                    event_manager.add_event({
                        'channel': 'game_queue',
                        'code': 'game_start_request',
                        'player_uid': self.get_player_by_protocol(event['protocol']),
                    })
                if request.command in (
                    uno_service.Command.PUT,
                    uno_service.Command.TAKE,
                    uno_service.Command.SKIP,
                    uno_service.Command.TAKE_TWO_AND_SKIP,
                    uno_service.Command.TAKE_FOUR_AND_SKIP,
                    uno_service.Command.LIST_CARDS,
                ):
                    event_manager.add_event({
                        'channel': 'game_command',
                        'player_uid': self.get_player_by_protocol(event['protocol']),
                        'command': event['data']
                    })
            if event['code'] == 'user_disconnected':
                player = self.get_player_by_protocol(event['protocol']),
                self.remove_player(player, event['protocol'])
                event_manager.add_event({
                    'channel': 'game_command',
                    'player_uid': self.get_player_by_protocol(event['protocol']),
                    'command': uno_service.Command.DISCONNECT
                })

        if event['channel'] == 'user_notification':
            protocol = self.get_protocol_by_player_uid(event['user_uid'])
            player = self.get_player_by_uid(event['user_uid'])
            if event.get('code') == NotificationType.ROUND_STARTED:
                player.round_uid = event['round_uid']
                event['player_uid'] = player.uid
            event.pop('user_uid')
            event.pop('channel')
            card = None
            if event.get('exception'):
                if event.get('not_allowed'):
                    response = uno_service.UnoService.get_notification.response(
                        not_allowed=event.get('not_allowed')
                    )
                if event.get('not_your_turn'):
                    response = uno_service.UnoService.get_notification.response(
                        not_your_turn=event.get('not_your_turn')
                    )
            else:
                notification_type = event.get('code')
                card = event.get('card')
                cards = event.get('cards')
                message = ''
                if event['code'] == NotificationType.YOUR_CARDS:
                    message = ';'.join(Card.simple_str(card) for card in cards)
                if event['code'] == NotificationType.ROUND_FINISHED:
                    message = 'winner {}'.format(event['winner'])

                notification = uno_service.Notification(
                    notification_type,
                    card=card,
                    message=message,
                    allowed_actions=event.get('allowed_actions', [])
                )
                response = uno_service.UnoService.get_notification.response(
                    success=notification
                )
            await protocol.send_message(response)


online_players = OnlinePlayers()
event_manager.subscribe('data_received', online_players)
event_manager.subscribe('user_notification', online_players)
