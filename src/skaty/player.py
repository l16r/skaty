from enum import Enum
from typing import Optional

from skaty.cards import Card
from skaty.exceptions import InvalidPlayError


class Player:
    _name: str
    _hand: list[Card]
    _played_cards: list[Card]

    def __init__(self, name: str, hand: Optional[list[Card]] = None):
        self._name = name
        self._hand = hand if hand is not None else []
        self._played_cards = []

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name

    @property
    def hand(self) -> list[Card]:
        return self._hand

    def all_cards(self) -> list[Card]:
        return self._hand + self._played_cards

    def add_card(self, card: Card):
        self._hand.append(card)

    def add_cards(self, cards: list[Card]):
        for c in cards:
            self.add_card(c)

    def play_card(self, card: Card):
        """
        Removes card from hand and adds to played history.
        """
        if card not in self.hand:
            raise InvalidPlayError(f"Card {card} not in hand.")
        self._hand.remove(card)
        self._played_cards.append(card)

    def undo_play_card(self, card: Card):
        """
        Moves card from played history back to hand.
        """
        if card not in self._played_cards:
            raise InvalidPlayError(f"Card {card} not in played cards.")
        self._played_cards.remove(card)
        self._hand.append(card)

    def clear_hand(self):
        """
        Reset hand and played cards.
        """
        self._hand.clear()
        self._played_cards.clear()
