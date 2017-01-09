# -*- coding: UTF-8 -*-
import unittest

from uno.game.deck import Deck, IncorrectCardError

from uno.protocol.service import uno_service
Card = uno_service.Card
Color = uno_service.Color
CardAction = uno_service.CardAction


class TestDeck(unittest.TestCase):

    def test_count_total(self):
        d = Deck()
        self.assertEqual(len(d._cards), 108)

    def test_count_by_color(self):
        d = Deck()
        self.assertEqual(len([i for i in d._cards if i.color == Color.RED]), 25)
        self.assertEqual(len([i for i in d._cards if i.color == Color.YELLOW]), 25)
        self.assertEqual(len([i for i in d._cards if i.color == Color.BLUE]), 25)
        self.assertEqual(len([i for i in d._cards if i.color == Color.GREEN]), 25)
        self.assertEqual(len([i for i in d._cards if i.color == Color.BLACK]), 8)

    def test_count_by_action(self):
        d = Deck()
        self.assertEqual(len([i for i in d._cards if i.action == CardAction.TAKE_TWO]), 8)
        self.assertEqual(len([i for i in d._cards if i.action == CardAction.REVERSE]), 8)
        self.assertEqual(len([i for i in d._cards if i.action == CardAction.SKIP]), 8)
        self.assertEqual(len([i for i in d._cards if i.action == CardAction.SET_COLOR]), 4)
        self.assertEqual(len([i for i in d._cards if i.action == CardAction.TAKE_FOUR_AND_SET_COLOR]), 4)

    def test_count_by_class(self):
        d = Deck()
        self.assertEqual(len([i for i in d._cards if i.action is None]), 108-32)
        self.assertEqual(len([i for i in d._cards if i.action is not None]), 32)

    def test_put_correct_card(self):
        d = Deck(cards=[
            Card(color=Color.RED, number=2),
            Card(color=Color.BLUE, number=2),
            Card(color=Color.BLUE, action=CardAction.SKIP),
            Card(color=Color.BLACK, action=CardAction.SET_COLOR, required_color=Color.YELLOW),
            Card(color=Color.YELLOW, number=5),
        ])
        while bool(d._cards):
            card = d.get_card()
            d.put_card(card)

    def test_cards_attr(self):
        d = Deck(cards=[Card(color=Color.RED, number=2)])
        self.assertEqual(len(d._cards), 1)

    def test_get_card(self):
        d = Deck(cards=[
            Card(color=Color.RED, number=2),
            Card(color=Color.BLUE, number=2),
        ])
        card = d.get_card()
        self.assertEqual(card, Card(color=Color.RED, number=2))

    def test_get_card_shuffle(self):
        d = Deck(
            cards=[],
            used_cards = [
                Card(color=Color.YELLOW, number=2),
                Card(color=Color.GREEN, number=2),
                Card(color=Color.BLUE, number=2),
                Card(color=Color.RED, number=2),
            ]
        )
        active_card = d.active_card
        card = d.get_card()
        self.assertEqual(len(d._cards), 2)
        self.assertEqual(len(d._used_cards), 1)
        self.assertEqual(d.active_card, Card(color=Color.YELLOW, number=2))


if __name__ == '__main__':
    unittest.main()
