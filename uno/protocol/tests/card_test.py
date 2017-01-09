
# -*- coding: UTF-8 -*-
import unittest

from uno.protocol.service import uno_service
Card = uno_service.Card
Color = uno_service.Color
CardAction = uno_service.CardAction


class TestCards(unittest.TestCase):

    def test_card_eq(self):
        self.assertEqual(
            Card(color=Color.RED, number=1),
            Card(color=Color.RED, number=1),
        )
        self.assertEqual(
            Card(color=Color.BLACK, action=CardAction.TAKE_TWO),
            Card(color=Color.BLACK, action=CardAction.TAKE_TWO),
        )
        self.assertNotEqual(
            Card(color=Color.BLACK, action=CardAction.TAKE_TWO),
            Card(color=Color.RED, number=3),
        )
        self.assertNotEqual(
            Card(color=Color.YELLOW, number=1),
            Card(color=Color.YELLOW, number=2),
        )
        self.assertNotEqual(
            Card(color=Color.YELLOW, number=1),
            Card(color=Color.RED, number=1),
        )

    def test_card_from_str(self):
        generated_card = Card.fromstr('black,-,set_color,red')
        self.assertEqual(
            Card(
                color=Color.BLACK,
                action=CardAction.SET_COLOR,
                required_color=Color.RED,
            ), generated_card
        )
        self.assertEqual(generated_card.required_color, Color.RED)

        generated_card = Card.fromstr('black,-,take_four_and_set_color,blue')
        self.assertEqual(
            Card(
                color=Color.BLACK,
                action=CardAction.TAKE_FOUR_AND_SET_COLOR,
                required_color=Color.BLUE,
            ), generated_card
        )
        self.assertEqual(generated_card.required_color, Color.BLUE)




if __name__ == '__main__':
    unittest.main()
