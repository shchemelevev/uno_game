# -*- coding: UTF-8 -*-
import random

from uno.protocol.service import uno_service
Card = uno_service.Card
Color = uno_service.Color
CardAction = uno_service.CardAction


simple_colors = (Color.BLUE, Color.YELLOW, Color.GREEN, Color.RED)


class IncorrectCardError(Exception):
    pass


class Deck(object):
    _cards = None
    _used_cards = None

    def __init__(self, cards=None, used_cards=None):
        if cards is None:
            self._generate_deck()
        else:
            self._cards = cards
        if used_cards is None:
            self._used_cards = list()
        else:
            self._used_cards = used_cards

    def _generate_deck(self):
        self._cards = list()
        # number cards
        for color in simple_colors:
            self._cards.append(Card(number=0, color=color))
            for number in range(1, 10):
                for i in range(2):
                    self._cards.append(Card(color=color, number=number))

        # action cards
        for color in simple_colors:
            for number in range(2):
                self._cards.append(Card(color=color, action=CardAction.SKIP))
                self._cards.append(
                    Card(color=color, action=CardAction.TAKE_TWO)
                )
                self._cards.append(Card(color=color, action=CardAction.REVERSE))

        # black cards
        for i in range(4):
            self._cards.append(
                Card(color=Color.BLACK, action=CardAction.SET_COLOR)
            )
            self._cards.append(
                Card(
                    color=Color.BLACK,
                    action=CardAction.TAKE_FOUR_AND_SET_COLOR
                )
            )

        random.shuffle(self._cards)

    def get_card(self):
        if len(self._cards) == 0:
            active_card = self._used_cards.pop(0)
            self._cards.extend(self._used_cards)
            self._used_cards.clear()
            random.shuffle(self._cards)
            self._used_cards.append(active_card)
        return self._cards.pop(0)

    @property
    def active_card(self):
        return self._used_cards[0]

    def put_card(self, card):
        self._used_cards.insert(0, card)
