from __future__ import annotations
from string import ascii_uppercase
from .data import getAllGameIDs, createNewGameDirectory, getSearchDict, getAllStopCodes, getAllLineColours, getAllZoneNumbers, getAllTeamIDs, getLiveDeckData, getRewardPlacementData, getAllSpecialAbilityCodes, clean, getLiveGameData, setLiveGameData, resetLiveGameData
from random import choice, sample, choices
from PIL.Image import Image
from typing import TYPE_CHECKING
from datetime import datetime, timedelta
if TYPE_CHECKING:
    from .stop import Stop
    from .line import Line
    from .team import Team
    from .zone import Zone
    from .special import Special
    from .action import Action
    from .map_images import drawMap


class Game:

    def __init__(self, id: str | None = None) -> None:
        if id == None:
            # generate new game id
            id = randomGameID()
            existing_game_ids = getAllGameIDs()
            while id in existing_game_ids:
                id = randomGameID()
            # create directory
            createNewGameDirectory(id)
            # initialise zone decks
            self._id = id
            for zone in self.all_zones:
                zone.createDeck()
        else:
            # capitalise id
            self._id = id.upper()

    @property
    def id(self) -> str:
        return self._id

    @property
    def all_teams(self) -> list[Team]:
        from .team import Team
        return [Team(id, self) for id in getAllTeamIDs(self._id)]

    @property
    def all_stops(self) -> list[Stop]:
        from .stop import Stop
        return [Stop(code, self) for code in getAllStopCodes()]

    @property
    def claimed_stops(self) -> list[Stop]:
        return [stop for stop in self.all_stops if stop.claimed]

    @property
    def unclaimed_stops(self) -> list[Stop]:
        return [stop for stop in self.all_stops if not stop.claimed]

    @property
    def locked_stops(self) -> list[Stop]:
        return [stop for stop in self.all_stops if stop.locked]

    @property
    def all_lines(self) -> list[Line]:
        from .line import Line
        return [Line(colour, self) for colour in getAllLineColours()]

    @property
    def claimed_lines(self) -> list[Line]:
        return [line for line in self.all_lines if line.claimed]

    @property
    def all_zones(self) -> list[Zone]:
        from .zone import Zone
        return [Zone(number, self) for number in getAllZoneNumbers()]

    @property
    def all_actions(self) -> list[Action]:
        from .action import Action
        return [Action.loadLive(deck_id, self) for deck_id in getLiveDeckData(self._id)]

    @property
    def in_progress(self) -> bool:
        return getLiveGameData(self._id)["in_progress"]

    @property
    def game_over(self) -> bool:
        # check if any team has won
        finished = any(team.has_won for team in self.all_teams)
        # end the game officially
        if finished and self.in_progress:
            # load live data
            live_data = getLiveGameData(self._id)
            # set end...
            live_data["in_progress"] = False
            live_data["end_time"] = datetime.now().timestamp()
            # save data
            setLiveGameData(self._id, live_data)
        return finished

    @property
    def total_game_time(self) -> timedelta | None:
        # load live data
        live_data = getLiveGameData(self._id)
        if not live_data["start_time"] or not live_data["end_time"]:
            return None
        # find difference in time!
        return datetime.fromtimestamp(live_data["end_time"]) - datetime.fromtimestamp(live_data["start_time"])

    @property
    def winner(self) -> Team:
        # check if any team has won and return that team
        return next(team for team in self.all_teams if team.has_won)    

    def map(self, observer: Team | None = None) -> Image:
        from .map_images import drawMap
        return drawMap(self, observer)

    def start(self) -> None:
        # do mulligan
        self.doMulligan()
        # load live data
        live_data = getLiveGameData(self._id)
        # set start...
        live_data["in_progress"] = True
        live_data["start_time"] = datetime.now().timestamp()
        # save data
        setLiveGameData(self._id, live_data)

    def reset(self) -> None:
        # unclaim everything!
        resetLiveGameData(self._id)
        for zone in self.all_zones:
            zone.createDeck()
        for team in self.all_teams:
            team.reset()


    def searchStop(self, search_term: str) -> Stop | None:
        stop = searchStop(search_term)
        if not stop:
            return None
        # link the stop to this game
        stop._game = self
        return stop

    def getStopFromCode(self, code: str) -> Stop:
        from .stop import Stop
        return Stop(code, self)

    def getTeamFromID(self, id: str) -> Team:
        from .team import Team
        return Team(id, self)

    def getZoneFromNumber(self, number: int) -> Zone:
        from .zone import Zone
        return Zone(number, self)

    def getLineFromColour(self, colour: str) -> Line:
        from .line import Line
        return Line(colour, self)

    def getTeamFromName(self, name: str) -> Team | None:
        search_term_clean = clean(name)
        search_term_clean = search_term_clean.removeprefix(
            'team ').removesuffix(' team')
        return next((team for team in self.all_teams
                     if clean(team.name).removeprefix('team ').removesuffix(' team') == search_term_clean
                     or clean(team.name) == search_term_clean
                     or team.colour == search_term_clean), None)

    def addTeam(self, name: str, colour: str) -> Team:
        from .team import Team
        # use team method
        return Team.new(self, name, colour)

    def dealSecret(self, team: Team, zone: Zone, exclude: Stop | None = None) -> Stop:
        all_secrets = []
        for other_team in self.all_teams:
            all_secrets.extend(other_team.retained_secrets)
        # get available stops
        available = [
            stop for stop in zone.stops_exclude_inner if not stop in all_secrets and not stop == exclude]
        # choose a random one
        chosen_stop = choice(available)
        # assign to the team
        team.addSecret(chosen_stop)
        # return a copy
        return chosen_stop

    def dealAllSecrets(self) -> None:
        from .zone import Zone
        # deal secrets in first 3 zones
        for team in self.all_teams:
            team.clearSecrets()
            for zone_number in range(1, 4):
                self.dealSecret(team, Zone(zone_number, self))

    def doMulligan(self) -> None:
        # so redo all of them that have been selected
        for team in self.all_teams:
            for mulliganed_secret in team.mulliganed_secrets:
                # remove the original secret
                team.removeSecret(mulliganed_secret)
                # redeal but it MUST be different
                self.dealSecret(
                    team, mulliganed_secret.inner_zone, mulliganed_secret)

    def assignRewards(self) -> None:
        # choose ALL THE STOPS according to data
        for stop in self.all_stops:
            stop.clearRewards()
        placements = getRewardPlacementData()

        def process(type: str, parts: list, count: int = -1):
            # choose a random selection, if required
            chosen_parts = sample(parts, count) if type == "choice" else parts
            for part in chosen_parts:
                if isinstance(part, str):
                    self.getStopFromCode(part).addReward()
                elif part["type"] == "special":
                    #assign special
                    self.getStopFromCode(part["stop"]).addSpecial(part["code"])
                else:
                    # recursion time!!
                    process(part["type"], part["parts"],
                            part["count"] if "count" in part else -1)
        # use recursive function to process placements
        process("all", placements)

    def __eq__(self, value: object) -> bool:
        try:
            return self._id == value._id
        except:
            return False


def randomGameID() -> str:
    # generate random 4-letter code in all caps
    return ''.join(choices(ascii_uppercase, k=4))


def searchStop(search_term: str) -> Stop | None:
    from .stop import Stop
    # filter search term for just letters and spaces
    search_term_clean = clean(search_term)
    # convert to code
    try:
        stop_code = getSearchDict()[search_term_clean]
    except:
        # does not correlate to a stop
        return None
    # check stop exists in this gam
    if not stop_code in getAllStopCodes():
        return None
    # return stop object
    return Stop(stop_code)


def getAllStops() -> list[Stop]:
    from .stop import Stop
    return [Stop(code) for code in getAllStopCodes()]


def getAllLines() -> list[Line]:
    from .line import Line
    return [Line(colour) for colour in getAllLineColours()]


def getAllZones() -> list[Zone]:
    from .zone import Zone
    return [Zone(number) for number in getAllZoneNumbers()]


def getAllActionCards() -> list[Action]:
    actions = []
    # get all unique actions
    for zone in getAllZones():
        for action in zone.start_deck:
            if not action in actions:
                actions.append(action)
    return actions


def getAllSpecialAbilities() -> list[Special]:
    from .special import Special
    return [Special(code) for code in getAllSpecialAbilityCodes()]
