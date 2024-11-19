from __future__ import annotations
from .data import getStaticSpecialAbilityData
from PIL.Image import Image
from .card import Card
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game import Game
    from .team import Team

class Special(Card):

    def __init__(self, code:str, game: Game | None = None) -> None:
        # set colour
        self._code: str = code
        # set game reference
        self._game: Game | None = game

    @property
    def game(self) -> Game:
        return self._game

    @property
    def code(self) -> str:
        return self._code
    
    @property
    def name(self) -> str:
        return getStaticSpecialAbilityData(self._code)["name"]

    @property
    def description(self) -> str:
        return getStaticSpecialAbilityData(self._code)["description"]

    @property
    def icon_name(self) -> str:
         return getStaticSpecialAbilityData(self._code)["icon"]
           
    def image(self, *args) -> Image:
        from .card_images import drawSpecialAbility
        # draw special ability
        return drawSpecialAbility(self)
    
    def __eq__(self, value: object) -> bool:
        if not value or not isinstance(value, Special):
            return False
        else:
            return self._code == value._code