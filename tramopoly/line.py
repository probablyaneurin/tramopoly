from __future__ import annotations
from .data import getStaticLineData, getColour
from PIL.Image import Image
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game import Game
    from .stop import Stop
    from .team import Team
    from .card_images import drawCollection, CollectionStyle


LINE_ORDER = {
    "brown":0,
    "pink":1,
    "navy":2,
    "green":3,
    "yellow":4,
    "purple":5,
    "blue":6,
    "orange":7,
    "red":8
}


class Line:

    def __init__(self, colour: str, game: Game | None = None) -> None:
        # set colour
        self._colour: str = colour
        # set game reference
        self._game: Game | None = game

    @property
    def game(self) -> Game:
        return self._game

    @property
    def colour(self) -> str:
        return self._colour

    @property
    def claimed(self) -> bool:
        return any(stop.locked_line == self for stop in self._game.all_stops)

    @property
    def owner(self) -> Team | None:
        # find one claimed stop
        stop = next(
            (stop for stop in self._game.all_stops if stop.locked_line == self), None)
        # use the owner of that stop
        return stop.owner if stop else None

    @property
    def locked_stops(self) -> list[Stop]:
        return [stop for stop in self._game.all_stops if stop.locked_line == self]

    @property
    def rgb_colour(self) -> tuple[int, int, int]:
        return getColour(getStaticLineData(self._colour)["colour"])

    @property
    def hex_colour(self) -> str:
        return getStaticLineData(self._colour)["colour"]

    @property
    def emoji(self) -> str:
        return getStaticLineData(self._colour)["emoji"]

    def is_claimable(self, team: Team) -> bool:
        # check which stops fit in which zones (consider special ability)
        return not self.claimed and enoughZonesCovered(team.free_stops_on_line(self), self.colour == "orange" and team.can_claim_orange)

    def is_valid_claim(self, stops: list[Stop]):
        # check which zones are covered (consider special ability)
        return enoughZonesCovered(stops,  self.colour == "orange" and stops[0].owner.can_claim_orange)

    def claim(self, stops: list[Stop]) -> None:
        # lock all the stops into this line
        for stop in stops:
            stop.lock(self)
        # check if game over
        self._game.game_over

    def unlock(self) -> None:
        # unlock all the stops
        for stop in self.locked_stops:
            stop.unlock()

    def image(self, observer: Team | None = None) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.locked_stops), CollectionStyle.STACKED, observer)

    def __eq__(self, value: object) -> bool:
        if not value or not isinstance(value, Line):
            return False
        else:
            return self._colour == value._colour
        
    def __lt__(self, other: object) -> bool:
        if not other or not isinstance(other, Line):
            return True
        else:
            return LINE_ORDER[self.colour] < LINE_ORDER[other.colour]


def enoughZonesCovered(stops: list[Stop], use_sections=False) -> bool:
    # start by ticking off the single-zone stops
    covered_zones = []
    available_multis = [0]*5
    for stop in stops:
        zone_string = str(stop.inner_zone.number) + \
            (stop.parent.code if use_sections else "")
        # tick off a zone if it's not on a border
        if not stop.on_zone_border and not zone_string in covered_zones:
            covered_zones.append(zone_string)
        # keep track of how many border stops are available to use
        elif stop.on_zone_border:
            available_multis[stop.inner_zone.number] += 1
    # check in case no multis are needed
    if len(covered_zones) >= 3:
        return True
    # use cornbrook as only way to decide for sections
    elif use_sections and "2PIC" in covered_zones and any(stop.code == "CNK" for stop in stops):
        return True
    # TODO: make this work for any case not just orange
    # try and use multis now (only on uncovered zones)
    for zone_number in [zone_number for zone_number in range(1, 5) if not zone_number in covered_zones]:
        # try use inner zone
        if available_multis[zone_number-1] > 0:
            available_multis[zone_number-1] -= 1
            covered_zones.append(zone_number)
        # try use outer zone
        elif available_multis[zone_number] > 0:
            available_multis[zone_number] -= 1
            covered_zones.append(zone_number)
    return len(covered_zones) >= 3
