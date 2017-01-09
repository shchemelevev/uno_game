# -*- coding: UTF-8 -*-

from uno.server.event_manager import event_manager
from uno.protocol.service import uno_service

from uno.protocol.service import uno_service
Card = uno_service.Card
Color = uno_service.Color
CardAction = uno_service.CardAction
NotificationType = uno_service.NotificationType


class TurnAction(object):
    input_list_len = 1
    command_id = None

    @classmethod
    def check_input(cls, command_request):
        if command_request.command != cls.command_id:
            return False
        return True

    @classmethod
    def check_condition(cls, command_request, uno_round):
        if not cls.check_input(command_request):
            return False
        return cls.check_main_condition(
            command_request.card,
            uno_round.deck.active_card,
            uno_round.current_player.cards,
            uno_round.taken_card
        )

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        return True

    @classmethod
    def update_round(cls, input_list, uno_round):
        pass


class PutCardAction(TurnAction):
    command_id = uno_service.Command.PUT
    input_list_len = 2

    @classmethod
    def check_condition(cls, command_request, uno_round):
        if command_request.command != cls.command_id:
            return False
        card = command_request.card
        has_card = False
        for item in uno_round.current_player.cards:
            if (
                item.color == card.color
                and item.action == item.action
                and item.number == item.number
            ):
                has_card = True
        if not has_card:
            return False
        if not cls.check_input(command_request):
            return False
        return cls.check_main_condition(
            command_request.card,
            uno_round.deck.active_card,
            uno_round.current_player.cards,
            uno_round.taken_card,
        )

    @classmethod
    def check_input(cls, command_request):
        if command_request.command != cls.command_id:
            return False
        if command_request.card is None:
            return False
        # TODO: check card
        return True

    @classmethod
    def update_round(cls, command_request, uno_round):
        card = command_request.card

        uno_round.current_player.remove_card(card)
        uno_round.deck.put_card(card)
        uno_round.notify_all(code=NotificationType.PLAYER_PUT_CARD, card=card)

        if card.action == CardAction.REVERSE:
            uno_round.change_direction()

        uno_round.set_next_player()
        card_actions = allowed_actions_for_card(card)
        uno_round.actions_list = card_actions

        uno_round.current_player.notify_user(
            code=NotificationType.YOUR_TURN,
            allowed_actions=uno_round.get_allowed_actions()
        )


class PutSameColorCardAction(PutCardAction):

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        return active_card.color == card.color


class PutSameNumberCardAction(PutCardAction):

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        return card.action is None and card.number == active_card.number


class PutRequiredColorCardAction(PutCardAction):

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        return card.color == active_card.required_color


class PutSetColorCardAction(PutCardAction):

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        # TODO: check required color setted
        return card.action == CardAction.SET_COLOR


class PutSkipCardAction(PutCardAction):

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        if card.action != CardAction.SKIP:
            return False
        return active_card.color == card.color


class PutTakenCardAction(PutCardAction):

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        if card != taken_card:
            return False
        if taken_card.action == CardAction.TAKE_FOUR_AND_SET_COLOR:
            return False
        if active_card.color == card.color:
            return True
        if active_card.number == card.number:
            return True
        if active_card.required_color == card.color:
            return True
        if active_card.action == CardAction.TAKE_TWO:
            return True
        return False


class PutTakeTwoCardAction(PutCardAction):

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        if card.action != CardAction.TAKE_TWO:
            return False
        if active_card.color == card.color:
            return True
        if active_card.required_color == card.color:
            return True
        return False


class PutTakeFourCardAction(PutCardAction):

    @classmethod
    def check_main_condition(cls, card, active_card, player_cards, taken_card):
        if card.action != CardAction.TAKE_FOUR_AND_SET_COLOR:
            return False
        # TODO: check required color setted
        for item in player_cards:
            if item.color != Color.BLACK and (
                item.color == active_card.color
                or item.number == active_card.number
                or item.color == active_card.required_color
            ):
                return False
        return True


class TakeAction(TurnAction):
    command_id = uno_service.Command.TAKE

    @classmethod
    def update_round(cls, command_request, uno_round):
        uno_round.actions_list = [ListCardsAction, PutTakenCardAction, SkipAction]

        card = uno_round.deck.get_card()
        uno_round.current_player.cards.append(card)
        uno_round.taken_card = card

        uno_round.current_player.notify_user(code=NotificationType.YOU_TOOK_CARD, card=card)
        uno_round.notify_all_except_current(
            code=NotificationType.PLAYER_TOOK_CARD,
            player=uno_round.current_player.uid
        )


class ListCardsAction(TurnAction):
    command_id = uno_service.Command.LIST_CARDS

    @classmethod
    def update_round(cls, command_request, uno_round):
        uno_round.current_player.notify_user(
            code=NotificationType.YOUR_CARDS,
            cards=uno_round.current_player.cards
        )


class SkipAction(TurnAction):
    command_id = uno_service.Command.SKIP

    @classmethod
    def update_round(cls, command_request, uno_round):
        card_actions = allowed_actions_for_card(uno_round.deck.active_card)
        uno_round.actions_list = [
            ListCardsAction,
            PutSameNumberCardAction, PutSameColorCardAction,
            PutSetColorCardAction, PutSkipCardAction, PutTakeTwoCardAction,
            PutTakeFourCardAction, TakeAction
        ]

        uno_round.current_player.notify_user(code=NotificationType.YOU_SKIPPED)
        uno_round.notify_all_except_current(
            code=NotificationType.PLAYER_SKIPPED,
            player=uno_round.current_player.uid
        )
        uno_round.set_next_player()
        uno_round.current_player.notify_user(
            code=NotificationType.YOUR_TURN,
            allowed_actions=uno_round.get_allowed_actions()
        )


class TakeAndSkipAction(TurnAction):
    take_count = 2

    @classmethod
    def update_round(cls, command_request, uno_round):
        uno_round.actions_list = [
            ListCardsAction, PutRequiredColorCardAction,
            PutSameNumberCardAction, PutSameColorCardAction,
            PutSetColorCardAction, PutSkipCardAction, PutTakeTwoCardAction,
            PutTakeFourCardAction, TakeAction
        ]

        for i in range(cls.take_count):
            card = uno_round.deck.get_card()
            uno_round.current_player.cards.append(card)
            uno_round.current_player.notify_user(
                code=NotificationType.YOU_TOOK_CARD, card=card
            )

        uno_round.notify_all_except_current(
            code=NotificationType.PLAYER_TOOK_CARDS,
            player=uno_round.current_player,
            cards_count=cls.take_count
        )
        uno_round.set_next_player()
        uno_round.current_player.notify_user(
            code=NotificationType.YOUR_TURN,
            allowed_actions=uno_round.get_allowed_actions()
        )


class TakeTwoAndSkipAction(TakeAndSkipAction):
    command_id = uno_service.Command.TAKE_TWO_AND_SKIP
    take_count = 2


class TakeFourAndSkipAction(TakeAndSkipAction):
    command_id = uno_service.Command.TAKE_FOUR_AND_SKIP
    take_count = 4


# TODO: move into CardAction object
def allowed_actions_for_card(card):
    if card.action is None:
        return [
            ListCardsAction, PutRequiredColorCardAction,
            PutSetColorCardAction, PutSkipCardAction, PutTakeTwoCardAction,
            PutTakeFourCardAction, TakeAction,
            PutSameNumberCardAction, PutSameColorCardAction,
        ]
    elif card.action == CardAction.SKIP:
        return [ListCardsAction, PutSkipCardAction, SkipAction]
    elif card.action == CardAction.TAKE_TWO:
        return [ListCardsAction, TakeTwoAndSkipAction, PutTakeTwoCardAction]
    elif card.action == CardAction.REVERSE:
        return [
            ListCardsAction,
            PutSkipCardAction, PutTakeTwoCardAction,
            PutTakeFourCardAction, TakeAction,
            PutSameColorCardAction, PutSetColorCardAction,
        ]
    elif card.action == CardAction.SET_COLOR:
        return [
            PutSetColorCardAction, PutRequiredColorCardAction,
            PutTakeTwoCardAction, TakeAction,
            PutTakeFourCardAction, ListCardsAction
        ]
    elif card.action == CardAction.TAKE_FOUR_AND_SET_COLOR:
        return [ListCardsAction, TakeFourAndSkipAction, PutTakeTwoCardAction]
