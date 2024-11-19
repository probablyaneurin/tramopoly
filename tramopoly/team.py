from __future__ import annotations
from .data import getLiveTeamData, setLiveTeamData, clean
from datetime import datetime
from PIL.Image import Image
from random import choice, shuffle
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game import Game
    from .stop import Stop, Challenge
    from .line import Line
    from .action import Action, OngoingCurse, ClearCurse, ActionType
    from .special import Special
    from .zone import Zone


class Team:

    def __init__(self, id: str, game: Game) -> None:
        # set id
        self._id: str = id
        # set game reference
        self._game: Game = game

    @property
    def game(self) -> Game:
        return self._game

    @property
    def id(self) -> str:
        return self._id

    @property
    def other_teams(self) -> list[Team]:
        return [team for team in self._game.all_teams if not team == self]

    @property
    def name(self) -> str:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # return team name
        return live_data["name"]

    @property
    def colour(self) -> str:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # return team name
        return live_data["colour"]

    @property
    def has_won(self) -> bool:
        # has claimed all secrets and has three lines
        return (all(stop.owner == self for stop in self.secrets)
                and len(self.claimed_lines) >= 3)

    @property
    def secrets(self) -> list[Stop]:
        from .stop import Stop
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # return all secret stops
        return [Stop(secret["code"], self._game) for secret in live_data["secrets"]]

    @property
    def mulliganed_secrets(self) -> list[Stop]:
        from .stop import Stop
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # return all secret stops that are about to be mulliganed
        return [Stop(secret["code"], self._game) for secret in live_data["secrets"] if "mulligan" in secret and secret["mulligan"]]

    @property
    def retained_secrets(self) -> list[Stop]:
        from .stop import Stop
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # return all secret stops that will not be mulliganed
        return [Stop(secret["code"], self._game) for secret in live_data["secrets"] if not "mulligan" in secret or not secret["mulligan"]]

    @property
    def revealed_secrets(self) -> list[Stop]:
        from .stop import Stop
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # return only revealed secret stops
        return [Stop(secret["code"], self._game) for secret in live_data["secrets"] if "revealed" in secret and secret["revealed"]]

    @property
    def unrevealed_secrets(self) -> list[Stop]:
        from .stop import Stop
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # return only revealed secret stops
        return [Stop(secret["code"], self._game) for secret in live_data["secrets"] if not "revealed" in secret or not secret["revealed"]]


    @property
    def claimed_stops(self) -> list[Stop]:
        return [stop for stop in self._game.all_stops if stop.owner == self]

    @property
    def claimed_unlocked_stops(self) -> list[Stop]:
        return [stop for stop in self._game.all_stops if stop.owner == self and not stop.locked]

    @property
    def claimed_lines(self) -> list[Line]:
        return [line for line in self._game.all_lines if line.owner == self]

    @property
    def claimable_lines(self) -> list[Line]:
        return [line for line in self._game.all_lines if line.is_claimable(self)]

    @property
    def available_actions(self) -> list[Action]:
        return [action for action in self._game.all_actions if action.dealt and action.owner == self and not action.used]

    @property
    def available_starting_actions(self) -> list[Action]:
        from .action import ActionType
        return [action for action in self.available_actions if not action.type == ActionType.COUNTER]

    @property
    def available_curses(self) -> list[Action]:
        from .action import ActionType
        return [action for action in self.available_actions if action.type == ActionType.CURSE]


    @property
    def reserved_actions(self) -> list[Action]:
        return [action for action in self._game.all_actions if action.reserved and action.owner == self]

    #TODO: fix this mess lol
    @property
    def in_challenge(self) -> bool:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # check in challenge (veto period also counts)
        if self.in_veto:
            return True
        elif "in_challenge" in live_data and live_data["in_challenge"]:
            return True

    @property
    def current_challenge(self) -> Challenge | None:
        from .stop import Challenge
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # find current challenge, or use default value
        if self.in_challenge:
            return Challenge(live_data["current_challenge"], self._game)
        else:
            return None

    @property
    def current_challenge_location(self) -> Stop | None:
        # check challenge exists
        current = self.current_challenge
        if not current:
            return None
        # now find the parent stop
        return current.location

    @property
    def in_veto(self) -> bool:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # check if not in veto period first
        if "in_veto" not in live_data or not live_data["in_veto"]:
            return False
        # now check if the veto end time has passed
        veto_end = datetime.fromtimestamp(live_data["veto_end"])
        if veto_end < datetime.now():
            # stop veto period and challenge period and say not in veto
            live_data["in_challenge"] = False
            live_data["current_challenge"] = None
            live_data["in_veto"] = False
            live_data["veto_end"] = None
            # save data
            setLiveTeamData(self._id, live_data, self._game._id)
            return False
        # must still be in veto otherwise
        else:
            return True

    @property
    def veto_end(self) -> datetime | None:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # check veto period end (use default if not in veto)
        if not self.in_veto:
            return None
        return datetime.fromtimestamp(live_data["veto_end"])

    ## SPECIAL ABILITIES ##

    @property
    def has_curse_immunity(self) -> bool:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # if this team has this special ability
        return "IMMUNITY" in live_data["special_abilities"]

    @property
    def has_reward_choice(self) -> bool:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # if this team has this special ability
        return "REWARDCHOICE" in live_data["special_abilities"]

    @property
    def can_claim_orange(self) -> bool:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # if this team has this special ability
        return "CLAIMORANGE" in live_data["special_abilities"]

    @property
    def may_progress(self) -> bool:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # make sure no current curses
        return len(live_data["clear_curses"]) == 0

    @property
    def special_abilities(self) -> list[Special]:
        from .special import Special
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # make sure no current curses
        return [Special(code, self._game) for code in live_data["special_abilities"]]

    @property
    def ongoing_curses(self) -> list[OngoingCurse]:
        from .action import Action
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # make sure we have
        curses = [Action.loadLive(curse["id"], self._game)
                  for curse in live_data["ongoing_curses"]]
        # make sure none have expired
        expired_curses = [curse for curse in curses if self.getCurseEndTime(curse) < datetime.now()]
        for curse in expired_curses:
            self.expireCurse(curse)
        # create the curses
        return [Action.loadLive(curse["id"], self._game)
                  for curse in live_data["ongoing_curses"]]

    @property
    def uncleared_curses(self) -> list[OngoingCurse]:
        from .action import Action
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # make sure no current curses
        return [Action.loadLive(deck_id, self._game) for deck_id in live_data["clear_curses"]]

    @property
    def paused_challenge(self) -> Challenge | None:
        live_data = getLiveTeamData(self._id, self._game._id)
        if ("in_challenge" not in live_data
                or not live_data["in_challenge"]) and "current_challenge" in live_data and live_data["current_challenge"]:
            return Challenge(live_data["current_challenge"], self._game)

    def getActionsByCode(self, code: str) -> list[Action]:
        return [action for action in self.available_actions if code == action.code]

    def getActionByCodeAndZone(self, code: str, zone: Zone) -> Action | None:
        try:
            options = [action for action in self.available_actions if action.code == code and action.zone == zone]
            return options[0]
        except:
            return None


    #nah actually move this to the secrets themselves maybe??
    def doDonation(self, choices: list[Stop]):
        # make it random!
        shuffle(choices)
        # send 'em
        for i, team in enumerate(self.other_teams):
            # and remove it from me
            self.removeSecret(choices[i])
            team.addSecret(choices[i])

    def doDropSecrets(self, choices: list[Stop]):
        #remove those from me!
        for secret in choices:
            self.removeSecret(secret)
        #yayyy

    def doAddSecrets(self):
        #deal some extra secrets!
        zone_2 = self._game.getZoneFromNumber(2)
        for team in self.other_teams:
            self._game.dealSecret(team, zone_2)
        #yayyy

    def free_stops_on_line(self, line: Line) -> list[Stop]:
        return [stop for stop in self.claimed_stops if line in stop.lines and not stop.locked]

    def counter_options(self, action: Action) -> list[Action]:
        from .action import ActionType
        if self == action.owner:
            return []
        return [card for card in self.available_actions if card.type == ActionType.COUNTER and card.playableSpecific(action)]

    def addSecret(self, stop: Stop) -> None:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # add new secret
        live_data["secrets"].append({
            "code": stop.code
        })
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def pauseChallenge(self) -> None:
        live_data = getLiveTeamData(self._id, self._game._id)
        # make sure they're in a challenge then say no
        live_data["in_challenge"] = False
        # save it!
        setLiveTeamData(self._id, live_data, self._game._id)
        

    def resumeChallenge(self) -> None:
        live_data = getLiveTeamData(self._id, self._game._id)
        # restart the challenge if you're waiting for one
        live_data["in_challenge"] = True
        # save it!!!
        setLiveTeamData(self._id, live_data, self._game._id)

    def removeSecret(self, stop: Stop) -> None:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # remove secret by keeping all the others
        live_data["secrets"] = [
            secret for secret in live_data["secrets"] if secret["code"] != stop.code]
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def chooseAction(self, action: Action) -> None:
        # make the choice to add it to the deck
        action.choose()
        # unreserve any other ones
        for choice in self.reserved_actions:
            choice.unreserve()

    def getClearableCurseByName(self, name: str) -> ClearCurse | None:
        # clean it up
        search_term_clean = clean(name)
        # determine which curse
        return next((curse for curse in self.uncleared_curses if clean(curse.title) == search_term_clean), None)

    def mulliganSecret(self, stop: Stop) -> None:
        live_data = getLiveTeamData(self._id, self._game._id)
        # add mulligan tag to secret
        live_data["secrets"] = [secret if secret["code"] != stop.code
                                else secret | {"mulligan": True}
                                for secret in live_data["secrets"]]
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def resetMulligan(self) -> None:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # return all secret stops that are about to be mulliganed
        for secret in live_data["secrets"]:
            if "mulligan" in secret and secret["mulligan"]:
                secret["mulligan"] = False
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def revealSecret(self, stop: Stop|None = None) -> None:
        if not self.unrevealed_secrets:
            return
        elif stop == None:
            stop = choice(self.unrevealed_secrets)
        live_data = getLiveTeamData(self._id, self._game._id)
        # add revealed tag to secret
        live_data["secrets"] = [secret if secret["code"] != stop.code
                                else secret | {"revealed": True}
                                for secret in live_data["secrets"]]
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def startChallenge(self, challenge: Challenge) -> bool:
        # check if veto
        if self.in_challenge or self.in_veto:
            return False
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # set new challenge
        live_data["in_challenge"] = True
        live_data["current_challenge"] = challenge.id
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)
        return True

    def completeChallenge(self) -> list[Action] | Action | Special | None:
        # claim the stop
        rewards = self.current_challenge_location.claim(self)
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # cancel current challenge
        live_data["in_challenge"] = False
        live_data["current_challenge"] = None
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)
        # return a copy of any reward (or choices of reward) earnt
        return rewards

    def vetoChallenge(self):
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # calculate veto period and start veto
        veto_period = self.current_challenge.veto_period
        veto_end: datetime = datetime.now() + veto_period
        # add veto period to data
        live_data["in_veto"] = True
        live_data["veto_end"] = int(veto_end.timestamp())
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def clearChallenge(self):
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # add veto period to data
        live_data["in_challenge"] = False
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)
  

    def addClearCurse(self, curse: ClearCurse) -> None:
        # stop the current challenge
        self.pauseChallenge()
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # add curse
        live_data["clear_curses"].append(curse._deck_id)
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def addOngoingCurse(self, curse: OngoingCurse) -> None:
        # no need to stop current challenge
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # add curse
        live_data["ongoing_curses"].append({
            "id": curse._deck_id,
            "end": int(curse.getEndTime().timestamp())
        })
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def getCurseEndTime(self, curse: OngoingCurse) -> datetime:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # find endtime
        curse_data = next(data for data in live_data["ongoing_curses"] if data["id"] == curse._deck_id)
        return datetime.fromtimestamp(curse_data["end"])

    def clearCurse(self, curse: ClearCurse) -> None:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # remove curse
        live_data["clear_curses"].remove(curse._deck_id)
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def expireCurse(self, curse: OngoingCurse) -> None:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # remove curse
        live_data["ongoing_curses"] = [
            data for data in live_data["ongoing_curses"] if not data["id"] == curse._deck_id]
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def clearSecrets(self) -> None:
        # get rid of them
        for secret in self.secrets:
            self.removeSecret(secret)

    def addSpecialAbility(self, special: Special) -> None:
        # load data
        live_data = getLiveTeamData(self._id, self._game._id)
        # add ability
        live_data["special_abilities"].append(special.code)
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)
        # make sure to clear curses if immunity
        if special.code == "IMMUNITY":
            # remove all current curses
            for curse in self.ongoing_curses:
                self.expireCurse(curse)
            for curse in self.uncleared_curses:
                self.clearCurse(curse)

    def new(game: Game, name: str, colour: str) -> Team:
        # determine number of teams and use this as id
        id = str(len(game.all_teams))
        # create new blank data
        live_data = {
            "name": name,
            "colour": colour,
            "secrets": [],
            "clear_curses": [],
            "ongoing_curses": [],
            "special_abilities": []
        }
        # save data
        setLiveTeamData(id, live_data, game._id)
        # now return new team object
        return Team(id, game)

    def reset(self) -> None:
        live_data = {
            "name": self.name,
            "colour": self.colour,
            "secrets": [],
            "clear_curses": [],
            "ongoing_curses": [],
            "special_abilities": []
        }
        # save data
        setLiveTeamData(self._id, live_data, self._game._id)

    def unlocked_stops_image(self, observer: Team | None = -1) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.claimed_unlocked_stops), CollectionStyle.HORIZONTAL, self if observer == -1 else observer)

    def locked_lines_image(self, observer: Team | None = -1) -> Image:
        from .card_images import drawLineCollection
        return drawLineCollection(sorted(self.claimed_lines), self if observer == -1 else observer)

    def secrets_image(self, observer: Team | None = -1) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.secrets), CollectionStyle.HORIZONTAL, self if observer == -1 else observer)

    def revealed_secrets_image(self, observer: Team | None = None) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.revealed_secrets), CollectionStyle.HORIZONTAL, observer)

    def unrevealed_secrets_image(self) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.unrevealed_secrets), CollectionStyle.HORIZONTAL, self)


    def available_actions_image(self) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.available_actions), CollectionStyle.HORIZONTAL, self)

    def available_starting_actions_image(self) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.available_starting_actions), CollectionStyle.HORIZONTAL, self)

    def available_curses_image(self) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.available_curses), CollectionStyle.HORIZONTAL, self)


    def counter_options_image(self, action: Action) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.counter_options(action)), CollectionStyle.HORIZONTAL, self)

    def special_abilities_image(self) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.special_abilities), CollectionStyle.HORIZONTAL)

    def current_curses_image(self) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(sorted(self.ongoing_curses + self.uncleared_curses), CollectionStyle.HORIZONTAL)

    def map(self) -> Image:
        return self._game.map(self)

    def __eq__(self, value: object) -> bool:
        try:
            return self._id == value._id
        except:
            return False
