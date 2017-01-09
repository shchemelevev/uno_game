enum CardAction {
    REVERSE = 1,
    SKIP = 2,
    SET_COLOR = 3,
    TAKE_TWO = 4,
    TAKE_FOUR_AND_SET_COLOR = 5
}

enum Color {
    BLACK = 1,
    BLUE = 2,
    GREEN = 3,
    YELLOW = 4,
    RED = 5
}


struct Card {
    1: optional Color color;
    2: optional i16 number;
    3: optional CardAction action;
    4: optional Color required_color;
}


enum Command {
    PUT = 1,
    TAKE = 2,
    SKIP = 3,
    TAKE_TWO_AND_SKIP = 4,
    TAKE_FOUR_AND_SKIP = 5,
    LOGIN = 6,
    LOGOUT = 7,
    START = 8,
    LIST_CARDS = 9,
    DISCONNECT = 10
}

enum NotificationType {
    NEW_CARD = 1,
    YOUR_TURN = 2,
    ACTIVE_CARD = 3,
    ROUND_STARTED = 4,
    CONNECTED = 5,
    YOU_TOOK_CARD = 6
    PLAYER_TOOK_CARD = 7,
    YOU_SKIPPED = 8,
    PLAYER_SKIPPED = 9,
    PLAYER_PUT_CARD = 10,
    PLAYER_TOOK_CARDS = 11,
    YOUR_CARDS = 12,
    ROUND_FINISHED = 13,
    PLAYER_DISCONNECTED = 14,
}

struct Notification {
    1: required NotificationType type,
    2: optional Card card,
    3: optional string message,
    4: optional list<Command> allowed_actions
}

exception ActionNotAllowed {
    1: optional string message;
}

exception NotYourTurn {
    1: optional string message;
}


service UnoService {
    void execute_command(
        1: required Command command,
        2: optional Card card,
        3: optional string username
    ),
    Notification get_notification()
    throws (1:ActionNotAllowed not_allowed, 2:NotYourTurn not_your_turn)
}
