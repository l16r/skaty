class SkatyError(Exception):
    """Base exception for all Skaty-related errors."""

    pass


class InvalidGameStateError(SkatyError):
    """Raised if an operation is performed in an invalid game state (e.g. playing a card before a trick starts)"""


class InvalidGameTypeError(SkatyError):
    """Raised when an invalid game type is passed as an argument (e.g. passing GameType.PASS for is_valid_game_declaration)."""


class InvalidBidError(SkatyError):
    """Raised when an illegal bid is made."""


class InvalidActionError(SkatyError):
    """Raised when an illegal action is tried (e.g. acting when not being the active player)."""


class InvalidDeclarationError(InvalidActionError):
    """Raised when a declaration violates the rules."""


class InvalidPlayError(InvalidActionError):
    """Raised when an illegal move is attempted (e.g. not following suit)."""


class NoCardsError(SkatyError):
    """Raised when no cards are passed where there should be some."""


class TrickNotFinishedError(InvalidGameStateError):
    """Raised when a trick with less than 3 cards is probed for a winner."""


class TrickFinishedError(InvalidGameStateError):
    """Raised when a card is added to a trick if it is finished."""


class IncompatibleRulesError(SkatyError):
    """Raised when two rule sets collide (e.g. comparing two cards based on different rule sets)."""
