# -*- coding: UTF-8 -*-
import unittest
from asyncio import QueueEmpty

from uno.game.ai import AILogic

from uno.server.event_manager import event_manager
from uno.protocol.service import uno_service
Card = uno_service.Card
Color = uno_service.Color
CardAction = uno_service.CardAction
Notification = uno_service.Notification
NotificationType = uno_service.NotificationType
Command = uno_service.Command


class TestAI(unittest.TestCase):

    def _get_all_events(self):
        events_list = list()
        try:
            while True:
                events_list.append(event_manager.event_queue.get_nowait())
        except QueueEmpty:
            pass
        return events_list

    def test_your_turn(self):
        ai = AILogic(None)
        ai.active_card = Card(color=Color.RED, number=1)
        ai.cards = [Card(color=Color.RED, number=2)]
        notification = Notification(
            type=NotificationType.YOUR_TURN,
            allowed_actions=[Command.PUT, Command.TAKE]
        )
        response = uno_service.UnoService.get_notification.response(
            success=notification
        )
        self.assertTrue(ai.process_notification(response))
        events = self._get_all_events()
        self.assertEqual(len(events), 1)
        data = events[0]['data']
        self.assertEqual(data.card, Card(color=Color.RED, number=2))

    def test_take_skip(self):
        ai = AILogic(None)
        ai.active_card = Card(color=Color.RED, number=1)
        ai.cards = [Card(color=Color.BLUE, number=2)]
        notification = Notification(
            type=NotificationType.YOUR_TURN,
            allowed_actions=[Command.PUT, Command.TAKE]
        )
        response = uno_service.UnoService.get_notification.response(
            success=notification
        )
        self.assertTrue(ai.process_notification(response))
        events = self._get_all_events()
        self.assertEqual(len(events), 1)
        data = events[0]['data']
        self.assertEqual(data.command, Command.TAKE)

        notification = Notification(
            type=NotificationType.YOU_TOOK_CARD,
            allowed_actions=[Command.PUT, Command.SKIP]
        )
        response = uno_service.UnoService.get_notification.response(
            success=notification
        )
        self.assertTrue(ai.process_notification(response))
        events = self._get_all_events()
        self.assertEqual(len(events), 1)
        data = events[0]['data']
        self.assertEqual(data.command, Command.SKIP)


if __name__ == '__main__':
    unittest.main()
