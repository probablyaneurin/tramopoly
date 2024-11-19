from __future__ import annotations
from random import choice, sample
from .data import getStartDeckData, getLiveDeckData, setLiveDeckData
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game import Game
    from .action import Action
    from .team import Team


class Zone:

    def __init__(self, number: int,  game: Game | None = None) -> None:
        # set number
        self._number: int = number
        # set game reference
        self._game: Game | None = game

    @property
    def game(self) -> Game:
        return self._game

    @property
    def number(self):
        return self._number

    @property
    def stops_exclude_inner(self):
        return [stop for stop in self._game.all_stops if stop.inner_zone == self]

    @property
    def deck(self) -> list[Action]:
        from .action import Action
        # load in live file
        live_deck = getLiveDeckData(self._game._id)
        actions: list[Action]= [Action.loadLive(id, self._game) for id in live_deck if live_deck[id]["zone"] == self._number]
        return [action for action in actions if not action.reserved and not action.dealt]

    @property
    def start_deck(self) -> list[Action]:
        from .action import Action
        # use the start deck list
        return [Action.load(code, self.number) for code in getStartDeckData(self._number)]

    def createDeck(self) -> None:
        # use the start deck list
        start_deck = getStartDeckData(self._number)
        # load in live file
        live_deck = getLiveDeckData(self._game._id)
        # create unique ids for each and add their info into the start deck
        counts = {}
        for action in start_deck:
            if (action + "-" + str(self.number)) in counts:
                counts[action + "-" + str(self.number)] += 1
            else:
                counts[action + "-" + str(self.number)] = 1
            # add it to the deck with this id
            live_deck |= {
                # will store if dealt within deck (and to who)
                action + "-" + str(self.number) + "-" + str(counts[action + "-" + str(self.number)]): {
                    "type": action,
                    "zone": self.number
                }
            }
        # save the deck
        setLiveDeckData(live_deck, self._game._id)

    def dealAction(self, team: Team) -> list[Action] | Action:
        # choose the correct number of action cards
        if team.has_reward_choice:
            options = sample(self.deck, 2)
            # deal it out to that team (but as a choice)
            for option in options:
                option.reserve(team)
            # return all options
            return options
        else:
            # deal out a single action card
            chosen_action = choice(self.deck)
            chosen_action.deal(team)
            # return a copy
            return chosen_action

    def __eq__(self, value: object) -> bool:
        try:
            return self._number == value._number
        except:
            return False

    def __lt__(self, value: object) -> bool:
        return self._number < value._number

    def __gt__(self, value: object) -> bool:
        return self._number > value._number

    def __le__(self, value: object) -> bool:
        return self._number <= value._number

    def __ge__(self, value: object) -> bool:
        return self._number >= value._number

    def __hash__(self) -> int:
        return self.number