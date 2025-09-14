class SkatyError(Exception):
    """Base exception for all Skaty-related errors."""

    pass


class InvalidGameStateError(SkatyError):
    """Raised if an operation is performed in an invalid game state (e.g. playing a card before a trick starts)"""


class InvalidPlayError(SkatyError):
    """Raised when an illegal move is attempted (e.g. not following suit)."""


class InvalidBidError(SkatyError):
    """Raised when an illegal bid is made."""
