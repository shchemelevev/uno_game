# -*- coding: UTF-8 -*-
import logging
import unittest

from asyncio import QueueEmpty

from uno.game.deck import Deck

from uno.game.uno_round import UnoRound, ActionNotAllowedError
from uno.game.actions import (
    allowed_actions_for_card, PutTakenCardAction, SkipAction, ListCardsAction,
    PutTakeFourCardAction

)

from uno.server.event_manager import event_manager

from uno.protocol.service import uno_service
Card = uno_service.Card
Color = uno_service.Color
CardAction = uno_service.CardAction
Command = uno_service.Command
NotificationType = uno_service.NotificationType

logger = logging.getLogger(__name__)


class TestTourActions(unittest.TestCase):

    def _find_event(self, notification_type, events_list):
        for event in events_list:
            print(event)
            if event['code'] == notification_type:
                return True
        return False

    def _get_all_events(self):
        events_list = list()
        try:
            while True:
                events_list.append(event_manager.event_queue.get_nowait())
        except QueueEmpty:
            pass
        return events_list

    def test_take_action(self):
        self._get_all_events()
        cards = list()
        for item in range(40):
            cards.append(Card(color=Color.RED, number=1))
        deck = Deck(cards=cards)

        uno_round = UnoRound(deck=deck)
        uno_round.add_player('1')
        uno_round.add_player('2')
        uno_round.start_round()
        events = self._get_all_events()

        old_current_player_index = uno_round.current_player_index
        player_cards_len = len(uno_round.current_player.cards)
        deck_cards_len = len(uno_round.deck._cards)
        player = uno_round.current_player
        events = self._get_all_events()

        uno_round.process_input(
            player,
            uno_service.UnoService.execute_command.request(Command.TAKE)
        )

        # current player equal
        self.assertEqual(
            uno_round.current_player_index, old_current_player_index
        )

        # card added to player cards
        self.assertEqual(player_cards_len+1, len(player.cards))

        # card removed from deck
        self.assertEqual(deck_cards_len-1, len(uno_round.deck._cards))

        # proper actions setted
        self.assertEqual(len(uno_round.actions_list), 3)
        for item in uno_round.actions_list:
            self.assertTrue(
                item in [PutTakenCardAction, SkipAction, ListCardsAction]
            )

        events = self._get_all_events()
        self.assertEqual(len(events), 2)
        self.assertTrue(self._find_event(NotificationType.YOU_TOOK_CARD, events))
        self.assertTrue(self._find_event(NotificationType.PLAYER_TOOK_CARD, events))

    def test_skip_action(self):
        self._get_all_events()
        cards = list()
        for item in range(40):
            cards.append(Card(color=Color.RED, number=1))
        deck = Deck(cards=cards)

        uno_round = UnoRound(deck=deck)
        uno_round.add_player('1')
        uno_round.add_player('2')
        uno_round.start_round()
        uno_round.process_input(
            uno_round.current_player,
            uno_service.UnoService.execute_command.request(Command.TAKE)
        )

        old_current_player_index = uno_round.current_player_index
        player_cards_len = len(uno_round.current_player.cards)
        deck_cards_len = len(uno_round.deck._cards)
        player = uno_round.current_player

        events = self._get_all_events()
        uno_round.process_input(
            uno_round.current_player,
            uno_service.UnoService.execute_command.request(Command.SKIP)
        )
        # current player changed
        self.assertNotEqual(
            uno_round.current_player_index, old_current_player_index
        )

        # card not removed from player
        self.assertEqual(player_cards_len, len(player.cards))

        # card not taken from deck
        self.assertEqual(deck_cards_len, len(uno_round.deck._cards))

        # proper actions setted
        self.assertEqual(len(uno_round.actions_list), 8)
        for item in uno_round.actions_list:
            self.assertTrue(
                item in allowed_actions_for_card(Card(color=Color.RED, number=1))
            )
        # player put card events
        events = self._get_all_events()
        self.assertEqual(len(events), 3)
        # your turn event
        self.assertTrue(self._find_event(NotificationType.PLAYER_SKIPPED, events))
        self.assertTrue(self._find_event(NotificationType.YOUR_TURN, events))

    def test_put_card_action(self):
        self._get_all_events()
        cards = list()
        for item in range(40):
            cards.append(Card(color=Color.RED, number=1))
        deck = Deck(cards=cards)

        uno_round = UnoRound(deck=deck)
        uno_round.add_player('1')
        uno_round.add_player('2')
        uno_round.start_round()
        events = self._get_all_events()

        old_current_player_index = uno_round.current_player_index
        player_cards_len = len(uno_round.current_player.cards)
        used_cards_len = len(uno_round.deck._used_cards)
        player = uno_round.current_player
        events = self._get_all_events()

        uno_round.process_input(
            uno_round.current_player,
            uno_service.UnoService.execute_command.request(
                Command.PUT, Card(color=Color.RED, number=1)
            )
        )

        # current player changed
        self.assertNotEqual(
            uno_round.current_player_index, old_current_player_index
        )

        # card removed from player
        self.assertEqual(player_cards_len-1, len(player.cards))

        # card added to deck
        self.assertEqual(used_cards_len+1, len(uno_round.deck._used_cards))

        # proper actions setted
        self.assertEqual(len(uno_round.actions_list), 8)
        for item in uno_round.actions_list:
            self.assertTrue(
                item in allowed_actions_for_card(Card(color=Color.RED, number=1))
            )
        # player put card events
        events = self._get_all_events()
        self.assertEqual(len(events), 3)
        # your turn event
        self.assertTrue(self._find_event(NotificationType.PLAYER_PUT_CARD, events))
        self.assertTrue(self._find_event(NotificationType.YOUR_TURN, events))

    def test_take_two_and_skip_action(self):
        self._get_all_events()
        cards = list()
        for item in range(40):
            cards.append(Card(color=Color.RED, number=1))
        deck = Deck(cards=cards)

        uno_round = UnoRound(deck=deck)
        uno_round.add_player('1')
        uno_round.add_player('2')
        uno_round.start_round()
        events = self._get_all_events()

        uno_round.current_player.cards.append(
            Card(color=Color.RED, action=CardAction.TAKE_TWO)
        )

        uno_round.process_input(
            uno_round.current_player,
            uno_service.UnoService.execute_command.request(
                Command.PUT, Card(color=Color.RED, action=CardAction.TAKE_TWO)
            )
        )

        with self.assertRaises(ActionNotAllowedError):
            uno_round.process_input(
                uno_round.current_player,
                uno_service.UnoService.execute_command.request(
                    Command.PUT, Card(color=Color.RED, number=1)
                )
            )

        old_current_player_index = uno_round.current_player_index
        player_cards_len = len(uno_round.current_player.cards)
        deck_cards_len = len(uno_round.deck._cards)
        player = uno_round.current_player
        events = self._get_all_events()

        uno_round.process_input(
            uno_round.current_player,
            uno_service.UnoService.execute_command.request(
                Command.TAKE_TWO_AND_SKIP
            )
        )

        # current player changed
        self.assertNotEqual(
            uno_round.current_player_index, old_current_player_index
        )

        # cards added to player
        self.assertEqual(player_cards_len+2, len(player.cards))

        # card removed from deck
        self.assertEqual(deck_cards_len-2, len(uno_round.deck._cards))

        # proper actions setted
        self.assertEqual(len(uno_round.actions_list), 8)
        for item in uno_round.actions_list:
            self.assertTrue(
                item in allowed_actions_for_card(Card(color=Color.RED, number=1))
            )
        # player put card events
        events = self._get_all_events()
        self.assertEqual(len(events), 4)
        # your turn event
        self.assertTrue(self._find_event(NotificationType.YOUR_TURN, events))
        self.assertTrue(self._find_event(NotificationType.YOU_TOOK_CARD, events))
        self.assertTrue(self._find_event(NotificationType.PLAYER_TOOK_CARDS, events))


class TestTourActions(unittest.TestCase):

    def test_put_take_four(self):
        card = Card(
            color=Color.BLACK, action=CardAction.TAKE_FOUR_AND_SET_COLOR,
            required_color=Color.BLUE
        )
        player_cards = [card, Card(color=Color.BLUE, number=3)]
        active_card = Card(color=Color.YELLOW, number=1)
        self.assertTrue(
            PutTakeFourCardAction.check_main_condition(
                card, active_card, player_cards, None
            )
        )

if __name__ == '__main__':
    unittest.main()
