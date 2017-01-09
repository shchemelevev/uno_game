from uno.server.event_manager import event_manager

from uno.protocol.service import uno_service
NotificationType = uno_service.NotificationType


class Player(object):
    uid = None
    cards = None

    def __init__(self, uid):
        self.cards = list()
        self.uid = uid

    def add_card(self, card):
        self.cards.append(card)
        self.notify_user(
            code=NotificationType.NEW_CARD,
            card=card
        )

    def remove_card(self, card):
        for item in self.cards:
            if (
                item.color == card.color
                and item.number == card.number
                and item.action == card.action
            ):
                self.cards.remove(item)
                break

    def notify_user(self, **kwargs):
        event = {
            'channel': 'user_notification',
            'user_uid': self.uid,
        }
        event.update(kwargs)
        event_manager.add_event(event)
