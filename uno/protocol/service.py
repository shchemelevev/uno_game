# -*- coding: UTF-8 -*-
import os

import thriftrw


file_dir = os.path.dirname(__file__)
uno_service = thriftrw.load(os.path.join(file_dir, 'protocol.thrift'))


class Card(uno_service.Card):
    ''' monkeypatch thrift class '''

    @property
    def cost(self):
        '''Карты с цифрой — стоимость по значению на карте.
           Карты действий (кроме черных) — 20 баллов.
           Черные карты действий — 50 баллов.
        '''
        if self.color == uno_service.Color.BLACK:
            return 50
        if self.action is not None:
            return 20
        return self.number

    @classmethod
    def simple_str(cls, card):
        if card is not None:
            return '{},{},{},{}'.format(
                uno_service.Color.name_of(card.color),
                card.number,
                uno_service.CardAction.name_of(card.action),
                uno_service.Color.name_of(card.required_color)
            )
        else:
            return ''

    @staticmethod
    def fromstr(data):
        color, number, action, required_color = data.split(',')
        if color == '-':
            color = None
        else:
            color = getattr(uno_service.Color, color.upper(), None)
        if number == '-':
            number = None
        else:
            number = int(number)
        if action == '-':
            action = None
        else:
            action = getattr(uno_service.CardAction, action.upper(), None)
        if required_color.strip() == '-':
            required_color = None
        else:
            required_color = getattr(uno_service.Color, required_color.strip().upper(), None)
        return Card(color, number, action, required_color)

    def __eq__(self, other):
        if isinstance(other, Card):
            attrs = ['color', 'number', 'action']
            result = True
            for attr in attrs:
                self_attr = getattr(self, attr)
                other_attr = getattr(other, attr)
                if self_attr is not None and self_attr != other_attr:
                    result = False
                    break
            return result
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

uno_service.Card = Card
