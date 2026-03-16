class SkatyError(Exception):
    """Base exception for all Skaty-related errors."""

    pass


class InvalidGameStateError(SkatyError):
    """Raised if an operation is performed in an invalid game state (e.g. playing a card before a trick starts)"""


class InvalidPlayError(SkatyError):
    """Raised when an illegal move is attempted (e.g. not following suit)."""


class InvalidDeclarationError(SkatyError):
    """Raised when a declaration violates the rules."""


class InvalidBidError(SkatyError):
    """Raised when an illegal bid is made."""


class InvalidActionError(SkatyError):
    """Raised when an illegal action is tried (e.g. acting when not being the active player)."""


class IncompatibleRulesError(SkatyError):
    """Raised when two rule sets collide (e.g. comparing two cards based on different rule sets)."""
