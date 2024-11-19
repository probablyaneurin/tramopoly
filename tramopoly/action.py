from __future__ import annotations

from tramopoly.team import Team
from .card import Card
from PIL.Image import Image
from datetime import datetime, timedelta
from enum import Enum
from .data import getLiveActionData, setLiveActionData, getStaticActionData, getStartDeckData, getAllZoneNumbers, setLivePendingCounter, getLivePendingCounter, getActionTypeData
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .team import Team
    from .game import Game
    from .stop import Stop
    from .zone import Zone


class ActionType(Enum):
    SPY = "spy"
    STEAL = "steal"
    COUNTER = "counter"
    CURSE = "curse"
    TRAP = "trap"


TYPE_ORDER = {
    ActionType.SPY: 0,
    ActionType.STEAL: 1,
    ActionType.COUNTER: 2,
    ActionType.CURSE: 3,
    ActionType.TRAP: 4
}


class Action(Card):

    def __init__(self, code: str, deck_id: str | None = None, game: Game | None = None) -> None:
        # set code
        self._code: str = code
        # set deck id
        self._deck_id: str | None = deck_id
        # set game reference
        self._game: Game | None = game
        self._force_zone = 0

    @property
    def game(self) -> Game:
        return self._game

    # check function (if not overriden, must be true)
    def playableTeam(self, victim: Team) -> bool:
        return True

    # check function (if not overriden, must be true)
    def playableSpecific(self) -> bool:
        return True

    # actual action function (including removing it from owner)
    def play(self, victim: Team) -> bool:
        # make sure there isn't currently a counter
        if self.has_expired_counter:
            return True
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # remove it from this team
        live_data["used"] = True
        # save data
        setLiveActionData(self._deck_id, live_data, self._game._id)
        # now check if it can be countered
        if len(victim.counter_options(self)) > 0:  # may be unsuccessful
            # set up pending counter (client may decide when to force play)
            setLivePendingCounter(
                self._deck_id,
                {
                    "victim": victim.id,
                    "expired": False
                },
                self._game._id
            )
            return False
        else:  # successful
            return True

    def counter(self, counter: Action):
        live_data = getLivePendingCounter(self._deck_id, self._game._id)
        live_data["expired"] = True
        live_data["countered_by"] = counter._deck_id
        setLivePendingCounter(self._deck_id, live_data, self._game._id)

    def expireCounter(self):
        live_data = getLivePendingCounter(self._deck_id, self._game._id)
        live_data["expired"] = True
        setLivePendingCounter(self._deck_id, live_data, self._game._id)

    @property
    def code(self) -> str:
        return self._code

    @property
    def deck_id(self) -> str:
        return self._deck_id

    @property
    def type(self) -> ActionType:
        # convert to enum
        return ActionType(getStaticActionData(self._code)["type"])

    @property
    def tagline(self) -> str:
        return getStaticActionData(self._code)["tagline"]

    @property
    def title(self) -> str:
        return getStaticActionData(self._code)["title"].upper()

    @property
    def rules(self) -> str:
        return getStaticActionData(self._code)["rules"]

    @property
    def zone(self) -> Zone:
        from .zone import Zone
        return Zone(getLiveActionData(self._deck_id, self._game._id)["zone"], self._game)

    @property
    def dealt(self) -> bool:
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # use default value of not dealt
        if "dealt" in live_data:
            return live_data["dealt"]
        else:
            return False

    @property
    def used(self) -> bool:
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # use default value of not dealt
        if "used" in live_data:
            return live_data["used"]
        else:
            return False

    @property
    def reserved(self) -> bool:
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # use default value of not dealt
        if "reserved" in live_data:
            return live_data["reserved"]
        else:
            return False

    @property
    def owner(self) -> Team:
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # use default value of no owner
        if "owner" in live_data:
            return Team(live_data["owner"], self._game)
        else:
            return None

    @property
    def icon(self) -> Image:
        from .card_images import loadIcon
        return loadIcon(getActionTypeData(self.type.value)["icon"] if self.type == ActionType.CURSE else getStaticActionData(self._code)["icon"])

    @property
    def emoji(self) -> str:
        return getActionTypeData(self.type.value)["emoji"] if self.type == ActionType.CURSE else getStaticActionData(self._code)["emoji"]

    @property
    def counter_chain(self) -> list[Action]:
        counter = getLivePendingCounter(self._deck_id, self._game._id)
        # combine with other counter
        if counter and "countered_by" in counter:
            return [self] + Action.loadLive(counter["countered_by"], self._game).counter_chain
        else:
            return [self]

    @property
    def has_pending_counter(self) -> bool:
        # make sure it hasn't expired
        counter = getLivePendingCounter(self._deck_id, self._game._id)
        return counter and (not "expired" in counter) or (not counter["expired"])

    @property
    def has_expired_counter(self) -> bool:
        # make sure it HAS expired
        counter = getLivePendingCounter(self._deck_id, self._game._id)
        return counter and "expired" in counter and counter["expired"]

    # static info!!
    @property
    def possible_zones(self) -> list[Zone]:
        from .zone import Zone
        # use just code
        zones = []
        for zone_number in getAllZoneNumbers():
            deck_data = getStartDeckData(zone_number)
            if self.code in deck_data:
                zones.append(Zone(zone_number))
        return zones

    def deal(self, team: Team):
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # set owner
        live_data["dealt"] = True
        live_data["owner"] = team.id
        # save live data
        setLiveActionData(self._deck_id, live_data, self._game._id)

    def reserve(self, team: Team):
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # set 'owner'
        live_data["reserved"] = True
        live_data["owner"] = team.id
        # save live data
        setLiveActionData(self._deck_id, live_data, self._game._id)

    def unreserve(self):
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # remove owner
        del live_data["reserved"]
        del live_data["owner"]
        # save live data
        setLiveActionData(self._deck_id, live_data, self._game._id)

    def choose(self):
        # load data
        live_data = getLiveActionData(self._deck_id, self._game._id)
        # owner has already been set when reserved
        del live_data["reserved"]
        live_data["dealt"] = True
        # save live data
        setLiveActionData(self._deck_id, live_data, self._game._id)

    # all types of action don't need inheritance to make this
    def image(self, *args) -> Image:
        from .card_images import drawAction
        # never changes regardless of viewer
        return drawAction(self)

    def counter_chain_image(self) -> Image:
        from .card_images import drawCollection, CollectionStyle
        return drawCollection(self.counter_chain, CollectionStyle.HORIZONTAL)

    # ACTUALLY LOAD IN THE CORRECT TYPE OF ACTION HERE!

    def loadLive(deck_id: str | None = None, game: Game | None = None) -> Action:
        # load data
        live_data = getLiveActionData(deck_id, game.id)
        # get code
        code = live_data["type"]
        # now check the code and create child class instance
        if code == "ANNOUNCEMENT":
            return Announcement(deck_id, game)
        elif code.startswith("CURSE-CLEAR"):
            return ClearCurse(code, deck_id, game)
        elif code.startswith("CURSE-ONGOING"):
            return OngoingCurse(code, deck_id, game)
        elif code == "INTERCHANGE":
            return Interchange(deck_id, game)
        elif code == "RAILROADED":
            return Railroaded(deck_id, game)
        elif code == "TICKETINSPECTION":
            return TicketInspection(deck_id, game)
        elif code == "CANCELLED":
            return Cancelled(deck_id, game)
        elif code == "REROUTED":
            return Rerouted(deck_id, game)
        elif code == "DERAILMENT":
            return Derailment(deck_id, game)

    def load(code: str, force_zone: int | None = None) -> Action:
        # check the code and create child class instance
        if code == "ANNOUNCEMENT":
            card = Announcement()
        elif code.startswith("CURSE-CLEAR"):
            card = ClearCurse(code)
        elif code.startswith("CURSE-ONGOING"):
            card = OngoingCurse(code)
        elif code == "INTERCHANGE":
            card = Interchange()
        elif code == "RAILROADED":
            card = Railroaded()
        elif code == "TICKETINSPECTION":
            card = TicketInspection()
        elif code == "CANCELLED":
            card = Cancelled()
        elif code == "REROUTED":
            card = Rerouted()
        elif code == "DERAILMENT":
            card = Derailment()
        card._force_zone = force_zone
        return card

    def __eq__(self, value: object) -> bool:
        # if both are live make sure they're the EXACT SAME
        if not value or not isinstance(value, Action):
            return False
        elif self._game and value._game:
            return self._deck_id == value._deck_id
        else:
            return self._code == value._code

    def __lt__(self, other: object) -> bool:
        if not other or not isinstance(other, Action):
            return super().__lt__(other)
        elif self.type != other.type:
            return TYPE_ORDER[self.type] < TYPE_ORDER[other.type]
        # BOTH are of the same action type
        # clearable curses come BEFORE ongoing curses
        elif isinstance(self, ClearCurse) and isinstance(other, OngoingCurse):
            return True
        elif isinstance(self, OngoingCurse) and isinstance(other, ClearCurse):
            return False
        # now they're NOT different curse types soooo use predetermined order
        elif self.code != other.code:
            return self.code < other.code
        # if in a game, determine what zone they came from!
        elif self.game and other.game:
            # now sort by zone...
            return self.zone < other.zone  # CAN BE EQUAL AND THAT'S OK
        else:
            # default to true
            return True


class Announcement(Action):

    def __init__(self, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__("ANNOUNCEMENT", deck_id, game)

    def playableTeam(self, victim: Team) -> bool:
        return victim != self.owner

    def playableSpecific(self, victim: Team) -> bool:
        return self.playableTeam(victim)

    def play(self, victim: Team) -> bool:
        # check if coutnerable
        if not super().play(victim):
            return False  # give a chance to be countered
        # now actually do the action (EXTERNAL)
        return True

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class TicketInspection(Action):

    def __init__(self, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__("TICKETINSPECTION", deck_id, game)

    def playableTeam(self, victim: Team) -> bool:
        return victim != self.owner

    def playableSpecific(self, victim: Team) -> bool:
        return self.playableTeam(victim)

    def play(self, victim: Team) -> bool:
        # check if counterable
        if not super().play(victim):
            return False  # give a chance to be countered
        # now actually do the action (EXTERNAL) - need secret choice
        return True

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class Curse(Action):

    def __init__(self, code: str, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__(code, deck_id, game)


class ClearCurse(Curse):

    def __init__(self, code: str, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__(code, deck_id, game)

    # check function
    def playableTeam(self, victim: Team) -> bool:
        # check if they have curse immunity!
        return victim != self.owner and not victim.has_curse_immunity

    def playableSpecific(self, victim: Team) -> bool:
        return self.playableTeam(victim)

    def play(self, victim: Team, rerouted: bool = False) -> bool:
        # check if counterable
        if not rerouted and not super().play(victim):
            return False  # give a chance to be countered
        # now actually do the action. ADD THIS CURSE TO THE TEAM
        victim.addClearCurse(self)
        return True

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class OngoingCurse(Curse):

    def __init__(self, code: str, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__(code, deck_id, game)

    # check function
    def playableTeam(self, victim: Team) -> bool:
        # check if they have curse immunity!
        return victim != self.owner and not victim.has_curse_immunity

    def playableSpecific(self, victim: Team) -> bool:
        return self.playableTeam(victim)

    def play(self, victim: Team, rerouted: bool = False) -> bool:
        # check if counterable
        if not rerouted and not super().play(victim):
            return False  # give a chance to be countered
        # now actually do the action. ADD THIS CURSE TO THE TEAM
        victim.addOngoingCurse(self)
        return True

    def getEndTime(self) -> datetime:
        # get data
        return datetime.now() + timedelta(minutes=getStaticActionData(self._code)["timer"])

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class Interchange(Action):

    def __init__(self, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__("INTERCHANGE", deck_id, game)

    # check function
    def playableTeam(self, victim: Team) -> bool:
        # make sure both teams have enough stops!
        return victim != self.owner and len(self.owner.claimed_unlocked_stops) >= 1 and len(victim.claimed_unlocked_stops) >= 1

    def playableSpecific(self, stop_to_take: Stop, stop_to_give: Stop | None = None) -> bool:
        # make sure each stop is unlocked
        if stop_to_give:
            return stop_to_take.owner and stop_to_give.owner and stop_to_give.owner != stop_to_take.owner and not stop_to_give.locked and not stop_to_take.locked
        else:
            return stop_to_take.owner and stop_to_take.owner != self.owner and len(self.owner.claimed_unlocked_stops) >= 1

    def play(self, stop_to_take: Stop, stop_to_give: Stop) -> bool:
        # check if counterable
        if not super().play(stop_to_take.owner):
            return False  # give a chance to be countered
        # now actually do the action. swap owners
        victim = stop_to_take.owner
        stop_to_take.claim(stop_to_give.owner)
        stop_to_give.claim(victim)
        return True

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class Railroaded(Action):

    def __init__(self, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__("RAILROADED", deck_id, game)

    # check function
    def playableTeam(self, victim: Team) -> bool:
        # make sure victim team has enough stops!
        return victim != self.owner and len(victim.claimed_unlocked_stops) >= 1

    def playableSpecific(self, stop_to_take: Stop) -> bool:
        # make sure the stop is unlocked
        return stop_to_take.owner and stop_to_take.owner != self.owner and not stop_to_take.locked

    def play(self, stop_to_take: Stop) -> bool:
        thief = self.owner
        # check if counterable
        if not super().play(stop_to_take.owner):
            return False  # give a chance to be countered
        # now actually do the action. steal the stop!
        stop_to_take.claim(thief)
        return True

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class Derailment(Action):

    def __init__(self, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__("DERAILMENT", deck_id, game)

    # check function
    def playableTeam(self, victim: Team) -> bool:
        # make sure victim team has enough stops!
        return victim != self.owner and len(victim.claimed_stops) >= 1

    def playableSpecific(self, stop_to_unclaim: Stop) -> bool:
        return bool(stop_to_unclaim.owner)

    def play(self, stop_to_unclaim: Stop) -> bool:
        # check if counterable
        if not super().play(stop_to_unclaim.owner):
            return False  # give a chance to be countered
        # now actually do the action. unclaim the stop!
        stop_to_unclaim.unclaim()
        return True

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class Cancelled(Action):

    def __init__(self, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__("CANCELLED", deck_id, game)

    def playableTeam(self, victim: Team) -> bool:
        return victim != self.owner

    def playableSpecific(self, action: Action) -> bool:
        # make sure the action is not more powerful
        return action.owner != self.owner and action.type != ActionType.CURSE and action.zone <= self.zone

    def play(self, action: Action) -> bool:
        # check if counterable
        if not super().play(action.owner):
            # give a chance to be countered (YES I KNOW IT'S CRAZY)
            return False
        # now actually do the action. counter it!
        action.counter(self)
        return True

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class Rerouted(Action):

    def __init__(self, deck_id: str | None = None, game: Game | None = None) -> None:
        super().__init__("REROUTED", deck_id, game)

    def playableTeam(self, victim: Team) -> bool:
        return victim != self.owner

    def playableSpecific(self, action: Action) -> bool:
        # make sure the action is a curse
        return action.owner != self.owner and action.type == ActionType.CURSE

    def play(self, curse: Action):
        # check if counterable
        if not super().play(curse.owner):
            # give a chance to be countered (YES I KNOW IT'S CRAZY LOLLL)
            return False
        # now actually do the action. counter it!
        curse.counter(self)
        # play the curse onto the owner of it!
        curse.play(curse.owner, rerouted=True)
        # yes, it was successful
        return True

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)
