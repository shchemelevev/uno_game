# -*- coding: UTF-8 -*-
import logging
import unittest
from asyncio import QueueEmpty

from uno.game.uno_round import UnoRound, NotYourTurnException
from uno.game.deck import Card, Deck
from uno.game.actions import allowed_actions_for_card
from uno.server.event_manager import event_manager

from uno.protocol.service import uno_service
Card = uno_service.Card
Color = uno_service.Color
CardAction = uno_service.CardAction
Command = uno_service.Command
NotificationType = uno_service.NotificationType

logger = logging.getLogger(__name__)


class TestRound(unittest.TestCase):

    def _get_all_events(self):
        events_list = list()
        try:
            while True:
                events_list.append(event_manager.event_queue.get_nowait())
        except QueueEmpty:
            pass
        return events_list

    def test_start_round(self):
        self._get_all_events()
        cards = list()
        for item in range(40):
            cards.append(Card(color=Color.RED, number=1))
        deck = Deck(cards=cards)

        uno_round = UnoRound(deck=deck)
        uno_round.add_player('1')
        uno_round.add_player('2')
        uno_round.start_round()

        self.assertNotEqual(uno_round.current_player_index, None)
        for i in range(2):
            self.assertEqual(len(uno_round.player_list[1].cards), 7)

        self.assertTrue(uno_round.deck.active_card)
        self.assertEqual(len(uno_round.actions_list), 9)
        for item in uno_round.actions_list:
            self.assertTrue(
                item in allowed_actions_for_card(Card(color=Color.RED, number=1))
            )

        events = self._get_all_events()
        logger.debug(events)
        self.assertEqual(len(events), 19)

    def test_not_your_turn(self):
        self._get_all_events()
        uno_round = UnoRound()
        player1 = uno_round.add_player('1')
        player2 = uno_round.add_player('2')
        uno_round.start_round()
        card_copy = uno_round.deck.active_card
        player1.cards = [card_copy]
        player2.cards = [card_copy]

        uno_round.current_player_index = 0
        with self.assertRaises(NotYourTurnException):
            uno_round.process_input(
                player2,
                uno_service.UnoService.execute_command.request(
                    Command.PUT,
                    Card(color=Color.RED, number=1)
                )
            )
        uno_round.process_input(
            player1,
            uno_service.UnoService.execute_command.request(
                Command.PUT,
                card_copy
            )
        )

    def test_win_conditions(self):
        self._get_all_events()
        uno_round = UnoRound()
        player1 = uno_round.add_player('1', 'human')
        player2 = uno_round.add_player('2', 'human')
        uno_round.start_round()
        uno_round.deck._used_cards = [Card(color=Color.RED, number=1)]
        uno_round.current_player_index = 0
        player1.cards = [
            Card(color=Color.RED, number=2),
            Card(color=Color.YELLOW, number=5),
        ]
        player2.cards = [
            Card(color=Color.YELLOW, number=2),
            Card(color=Color.RED, number=5),
        ]
        uno_round.process_input(player1,
            uno_service.UnoService.execute_command.request(
                Command.PUT, player1.cards[0] # red,2
            )
        )
        uno_round.process_input(player2,
            uno_service.UnoService.execute_command.request(
                Command.PUT, player2.cards[0] # yellow,2
            )
        )
        events = self._get_all_events()
        uno_round.process_input(player1,
            uno_service.UnoService.execute_command.request(
                Command.PUT, player1.cards[0]  # yellow, 5
            )
        )
        events = self._get_all_events()
        for ev in events:
            print(ev)
        self.assertTrue([i for i in events if i['code'] == NotificationType.ROUND_FINISHED])

    def test_set_next_player(self):
        self._get_all_events()
        uno_round = UnoRound()
        player1 = uno_round.add_player('1')
        player2 = uno_round.add_player('2')
        player3 = uno_round.add_player('3')
        uno_round.current_player_index = 0
        self.assertEqual(player1, uno_round.current_player)
        uno_round.set_next_player()
        self.assertEqual(player2, uno_round.current_player)
        uno_round.set_next_player()
        self.assertEqual(player3, uno_round.current_player)
        uno_round.set_next_player()
        self.assertEqual(player1, uno_round.current_player)

if __name__ == '__main__':
    unittest.main()
