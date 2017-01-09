# -*- coding: UTF-8 -*-
import random
import logging

from uno.game.actions import (
    PutRequiredColorCardAction, PutSameColorCardAction, PutSameNumberCardAction,
    PutSetColorCardAction, PutSkipCardAction, PutTakenCardAction,
    PutTakeTwoCardAction, PutTakeFourCardAction, TakeAction, SkipAction,
    TakeTwoAndSkipAction, TakeFourAndSkipAction
)

from uno.server.event_manager import event_manager
from uno.protocol.service import uno_service
NotificationType = uno_service.NotificationType
Command = uno_service.Command
Color = uno_service.Color

logger = logging.getLogger(__name__)


class NewCardProcessor(object):
    notification_type = NotificationType.NEW_CARD

    @classmethod
    def process(cls, logic_object, notification):
        logic_object.cards.append(notification.card)


class YouTookCardProcessor(object):
    notification_type = NotificationType.YOU_TOOK_CARD

    @classmethod
    def process(cls, logic_object, notification):
        # always skip after take
        logic_object.cards.append(notification.card)
        request = uno_service.UnoService.execute_command.request(
            Command.SKIP
        )
        event_manager.add_event({
            'channel': 'data_received',
            'code': 'data_received',
            'data': request,
            'protocol': logic_object.protocol
        })
        return True


class PlayerPutCardProcessor(object):
    notification_type = NotificationType.PLAYER_PUT_CARD

    @classmethod
    def process(cls, logic_object, notification):
        logic_object.active_card = notification.card


class RoundStartedProcessor(object):
    notification_type = NotificationType.ROUND_STARTED

    @classmethod
    def process(cls, logic_object, notification):
        logger.debug('round started')
        logger.debug('ai cards %s', logic_object.cards)


class ActiveCardProcessor(object):
    notification_type = NotificationType.ACTIVE_CARD

    @classmethod
    def process(cls, logic_object, notification):
        logic_object.active_card = notification.card


class YourTurnProcessor(object):
    notification_type = NotificationType.YOUR_TURN

    @classmethod
    def process(cls, logic_object, notification):
        print('--ai cards'*10)
        print(logic_object.cards)
        for action in logic_object.actions:
            if action.command_id in notification.allowed_actions:
                print(action)
                if action.command_id == Command.PUT:
                    for card in logic_object.cards:
                        if action.check_main_condition(
                            card, logic_object.active_card, logic_object.cards, None
                        ):
                            # random color for black cards
                            if card.color == Color.BLACK:
                                card.required_color = random.choice([
                                    Color.BLUE, Color.YELLOW, Color.RED, Color.GREEN
                                ])
                            # remove card

                            request = uno_service.UnoService.execute_command.request(
                                action.command_id,
                                card=card
                            )
                            event_manager.add_event({
                                'channel': 'data_received',
                                'code': 'data_received',
                                'data': request,
                                'protocol': logic_object.protocol
                            })
                            logic_object.remove_card(card)
                            return True
                else:
                    request = uno_service.UnoService.execute_command.request(
                        action.command_id
                    )
                    event_manager.add_event({
                        'channel': 'data_received',
                        'code': 'data_received',
                        'data': request,
                        'protocol': logic_object.protocol
                    })
                    return True
        return False


class AILogic(object):
    actions = [SkipAction,
        TakeTwoAndSkipAction, TakeFourAndSkipAction,
        PutSkipCardAction, PutRequiredColorCardAction,
        PutSameColorCardAction, PutSameNumberCardAction,
        PutSetColorCardAction, PutTakeTwoCardAction,
        PutTakeFourCardAction, TakeAction,
        # PutTakenCardAction, take than skip
    ]
    notification_processors = [
        NewCardProcessor, RoundStartedProcessor, YourTurnProcessor,
        ActiveCardProcessor, PlayerPutCardProcessor, YouTookCardProcessor
    ]
    cards = None
    active_card = None
    protocol = None

    def __init__(self, protocol):
        self.cards = list()
        self.protocol = protocol

    def remove_card(self, card):
        for item in self.cards:
            if item == card:
                self.cards.remove(item)
                break

    def process_notification(self, notification):
        if notification.success:
            for processor in self.notification_processors:
                if processor.notification_type == notification.success.type:
                    return processor.process(self, notification.success)
