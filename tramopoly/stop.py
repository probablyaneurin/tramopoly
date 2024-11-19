
from __future__ import annotations
from .data import getLiveStopData, getStaticStopData, getChallengeData, setLiveStopData, clean
from .card import Card
from datetime import timedelta
from pathlib import Path
from PIL.Image import Image
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .line import Line
    from .zone import Zone
    from .game import Game, getAllStops
    from .team import Team
    from .action import Action
    from .special import Special
    from .map_images import IconType

STANDARD_VETO = 10


class Stop(Card):

    def __init__(self, code: str, game: Game | None = None) -> None:
        # set code
        self._code: str = code
        # set game reference
        self._game: Game | None = game

    @property
    def code(self) -> str:
        return self._code

    @property
    def game(self) -> Game:
        return self._game

    @property
    def parent(self) -> Stop:
        # all zone 1 stops have st peters square as parent
        if self.inner_zone.number == 1 and not self.on_zone_border:
            return self._game.getStopFromCode("SPS")
        else:
            # load data
            return Stop(getStaticStopData(self._code)["parent"], self._game)

    @property
    def name(self) -> str:
        return getStaticStopData(self._code)["name"]

    @property
    def lines(self) -> list[Line]:
        from .line import Line
        return [Line(colour, self._game) for colour in getStaticStopData(self._code)["lines"]]

    @property
    def inner_zone(self) -> Zone:
        from .zone import Zone
        return Zone(getStaticStopData(self._code)["inner_zone"], self._game)

    @property
    def on_zone_border(self) -> bool:
        return getStaticStopData(self._code)["on_zone_border"]

    @property
    def zone_string(self) -> str:
        return str(self.inner_zone.number) if not self.on_zone_border else str(self.inner_zone.number) + "/" + str(self.inner_zone.number + 1)

    @property
    def claimed(self) -> bool:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # use default value of not claimed
        if "claimed" in live_data:
            return live_data["claimed"]
        else:
            return False

    @property
    def owner(self) -> Team | None:
        from .team import Team
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # use default value of no owner
        if "owner" in live_data:
            # create team object
            return Team(live_data["owner"], self._game)
        else:
            return None

    @property
    def locked(self) -> bool:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # use default value of not locked
        if "locked" in live_data:
            return live_data["locked"]
        else:
            return False

    @property
    def locked_line(self) -> Line | None:
        from .line import Line
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # use default value of no locked line
        if "locked_line" in live_data:
            # create line object
            return Line(live_data["locked_line"], self._game)
        else:
            return None

    @property
    def has_reward(self) -> bool:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # make sure it has a reward
        if "has_reward" in live_data and live_data["has_reward"]:
            return True
        else:
            return False

    @property
    def special(self) -> Special | None:
        from .special import Special
        # load static data
        live_data = getLiveStopData(self._code, self._game._id)
        if "special" in live_data and not self.special_used:
            return Special(live_data["special"], self._game)

    @property
    def special_used(self) -> bool:
        if not self._game:
            return False
        # load live data
        live_data = getLiveStopData(self._code, self._game._id)
        # determine if used (default value)
        if "special_used" in live_data:
            return live_data["special_used"]
        else:
            return False

    @property
    def challenges(self) -> list[Challenge]:
        return [Challenge(id, self._game) for id in getStaticStopData(self._code)["challenges"]]

    def map_icon(self, observer: Team | None = None) -> IconType:
        from .map_images import IconType
        if not self._game:
            return IconType.NONE
        elif self.special:
            return IconType.SPECIAL_ABILITY
        elif self.locked:
            return IconType.LOCKED_YOU if observer == self.owner else IconType.LOCKED_OTHER
        elif self.claimed:
            return IconType.CLAIMED_YOU if observer == self.owner else IconType.CLAIMED_OTHER
        elif self.has_reward:
            return IconType.REWARD
        elif observer and self in observer.secrets:
            return IconType.SECRET
        else:
            return IconType.NONE

    # TODO: gain special abilities

    # returns action card (TODO: or special ability) if it has been earnt

    def getChallengeFromName(self, name: str) -> Challenge | None:
        search_term_clean = clean(name)
        return next((challenge for challenge in self.challenges
                     if clean(challenge.title) == search_term_clean), None)

    def claim(self, team: Team) -> list[Action] | Action | Special | None:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # set new owner
        live_data["claimed"] = True
        live_data["owner"] = team.id
        result = None
        # check for rewards and special abilities
        if "has_reward" in live_data and live_data["has_reward"]:
            # deal out reward and return a copy
            live_data["has_reward"] = False
            result = self.inner_zone.dealAction(team)
        elif self.special:
            team.addSpecialAbility(self.special)
            result = self.special
            live_data["special_used"] = True
        # save data
        setLiveStopData(self._code, live_data, self._game._id)
        # kick any other teams out...
        for other_team in team.other_teams:
            if other_team.current_challenge_location == self and not other_team.in_veto:
                # remove without consequence
                other_team.clearChallenge()
        # check if game over
        self._game.game_over
        return result

    def unclaim(self) -> None:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # remove claim
        live_data["claimed"] = False
        del live_data["owner"]
        # save data
        setLiveStopData(self._code, live_data, self._game._id)
        # make sure it isn't locked
        if "locked" in live_data and live_data["locked"]:
            self.locked_line.unlock()

    def lock(self, line: Line) -> None:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # set new locked line
        live_data["locked"] = True
        live_data["locked_line"] = line.colour
        # save data
        setLiveStopData(self._code, live_data, self._game._id)

    def unlock(self) -> None:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # remove locked line
        live_data["locked"] = False
        del live_data["locked_line"]
        # save data
        setLiveStopData(self._code, live_data, self._game._id)

    def addReward(self) -> None:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # add reward flag
        live_data["has_reward"] = True
        # save data
        setLiveStopData(self._code, live_data, self._game._id)

    def addSpecial(self, code: str) -> None:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # add special ability
        live_data["special"] = code
        # save data
        setLiveStopData(self._code, live_data, self._game._id)

    def clearRewards(self) -> None:
        # load data
        live_data = getLiveStopData(self._code, self._game._id)
        # remove reward flag
        if "has_reward" in live_data:
            del live_data["has_reward"]
        elif "special" in live_data:
            del live_data["special"]
            if "special_used" in live_data:
                del live_data["special_used"]
        # save data
        setLiveStopData(self._code, live_data, self._game._id)

    def image(self, observer: Team | None = None) -> Image:
        from .card_images import drawStop
        return drawStop(self, observer)

    def full_image(self, observer: Team | None = None) -> Image:
        # include special ability
        if self._game and self.special and not self.special_used:
            from .card_images import drawCollection, CollectionStyle
            return drawCollection([self, self.special], CollectionStyle.HORIZONTAL, observer)
        else:
            return self.image(observer)

    def __eq__(self, value: object) -> bool:
        if not value or not isinstance(value, Stop):
            return False
        else:
            return self._code == value._code

    def __lt__(self, other: object) -> bool:
        if not other or not isinstance(other, Stop):
            return super().__lt__(other)
        # by ZONE
        elif self.inner_zone != other.inner_zone:
            return self.inner_zone.number < other.inner_zone.number
        # in the same zone...
        elif self.on_zone_border and not other.on_zone_border:
            return True
        # alphabetical BY NAME
        else:
            return self.name.lower() < other.name.lower()


class Challenge:

    def __init__(self, id: str, game: Game) -> None:
        # set id
        self._id = id
        # set game reference
        self._game = game

    @ property
    def game(self) -> Game:
        return self._game

    @ property
    def id(self) -> str:
        return self._id

    @ property
    def location(self) -> Stop:
        # work this out from stops
        if self._game:
            return next(stop for stop in self._game.all_stops if self in stop.challenges)
        else:
            from .game import getAllStops
            return next(stop for stop in getAllStops() if self in stop.challenges)

    @ property
    def title(self) -> str:
        return getChallengeData(self._id)["title"]

    @ property
    def content(self) -> str:
        return getChallengeData(self._id)["content"]

    @ property
    def authors(self) -> list[str] | None:
        static_data = getChallengeData(self._id)
        return static_data["authors"] if "authors" in static_data and static_data["authors"] else None

    @ property
    def veto_period(self) -> timedelta:
        # get data
        static_data = getChallengeData(self._id)
        # check if specific veto length specified
        if "veto_minutes" in static_data:
            return timedelta(minutes=getChallengeData(self._id)["veto_minutes"])
        # otherwise always default to 8 minutes
        else:
            return timedelta(minutes=STANDARD_VETO)

    def __eq__(self, value: object) -> bool:
        return self._id == value._id
