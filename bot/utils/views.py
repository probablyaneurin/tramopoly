from discord import Interaction
from tramopoly import Action, Game, Team, Stop, Line, Zone, ActionType
from discord.ui import Select, View
from random import choice, sample

DEFAULT = "-"

# ELEMENTS


class ActionDropdown(Select):

    def __init__(self, parent: View, options: list[Action], default_label=None, default_description="") -> None:
        super().__init__(placeholder="Choose an action card...")
        self._parent = parent
        for option in options:
            self.add_option(
                label=option.title + f" [Zone {option.zone.number}]",
                value=option.deck_id,
                description=truncate(option.rules),
                emoji=option.emoji
            )
        if default_label:
            self.add_option(
                label=default_label,
                value=DEFAULT,
                description=truncate(default_description),
                emoji="🔴"
            )

    def chosen_action(self, game: Game) -> Action | None:
        if self.values and not self.values[0] == DEFAULT:
            return Action.loadLive(self.values[0], game)

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        # ignore interaction
        self._parent.update()


class StopDropdown(Select):

    def __init__(self, parent: View, options: list[Stop], min_count: int = 0, max_count: int = 0, default_label=None, default_description="") -> None:
        super().__init__(placeholder=f"Choose stop{'s' if max_count != 1 else ''}...", min_values=min_count, max_values=max_count if max_count >= 1 else len(options))
        self._parent = parent
        for option in options:
            self.add_option(
                label=option.name,
                value=option.code,
                description=f"Zone {option.zone_string}",
                emoji="📌"
            )
        if default_label:
            self.add_option(
                label=default_label,
                value=DEFAULT,
                description=truncate(default_description),
                emoji="🔴"
            )

    def chosen_stops(self, game: Game) -> list[Stop]:
        if self.values and not self.values[0] == DEFAULT:
            return [Stop(code, game) for code in self.values]
        return []

    def chosen_stop(self, game: Game) -> Stop | None:
        if self.values and not self.values[0] == DEFAULT:
            return Stop(self.values[0], game)

    # your first choice will literally just be taken
    async def callback(self, interaction: Interaction):
        # ignore interaction
        await interaction.response.defer()
        self._parent.update()


class TeamDropdown(Select):

    def __init__(self, parent: View, options: list[Team], default_label=None, default_description="") -> None:
        super().__init__(placeholder="Choose a team...")
        self._parent = parent
        for option in options:
            self.add_option(
                label=option.name,
                value=option.id,
                emoji="👥"
            )
        if default_label:
            self.add_option(
                label=default_label,
                value=DEFAULT,
                description=truncate(default_description),
                emoji="🔴"
            )

    def chosen_team(self, game: Game) -> Action | None:
        if self.values and not self.values[0] == DEFAULT:
            return game.getTeamFromID(self.values[0])

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        # ignore interaction
        self._parent.update()


class ZoneDropdown(Select):

    def __init__(self, parent: View, options: list[Zone]) -> None:
        super().__init__(placeholder="Choose a zone...")
        self._parent = parent
        for option in options:
            self.add_option(
                label=f"Zone {option.number}",
                value=str(option.number),
                emoji=["1️⃣", "2️⃣", "3️⃣", "4️⃣"][option.number-1]
            )

    def chosen_zone(self, game: Game) -> Zone | None:
        if self.values and not self.values[0] == DEFAULT:
            return Zone(int(self.values[0]), game)

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        # ignore interaction
        self._parent.update()


# VIEWS

class RewardChoice(View):

    def __init__(self, options: list[Action]):
        self._dropdown = ActionDropdown(self, options)
        self._game = options[0]._game
        # always do a two minute timeout...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    @property
    def chosen_reward(self) -> Action | None:
        return self._dropdown.chosen_action(self._game)

    def update(self) -> None:
        if self._dropdown.chosen_action(self._game):
            self.disable_all_items()
            self.stop()


class MulliganChoice(View):

    def __init__(self, team: Team):
        self._dropdown = StopDropdown(self, team.secrets)
        self._game = team._game
        self._team = team
        # allow 5 minutes to choose...
        super().__init__(self._dropdown, disable_on_timeout=True)

    def addMulliganChoices(self) -> None:
        # undo the previous one
        self._team.resetMulligan()
        # mulligan them all!
        for stop in self._dropdown.chosen_stops(self._game):
            self._team.mulliganSecret(stop)

    # update mulligan choices
    def update(self) -> None:
        self.addMulliganChoices()


class LineClaimChoice(View):

    def __init__(self, team: Team, line: Line):
        self._dropdown = StopDropdown(
            self, team.free_stops_on_line(line), 3, 3)
        self._game = team.game
        # use 2 minute timer
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    def update(self) -> None:
        # stop if actually finished
        if len(self._dropdown.chosen_stops(self._game)) == 3:
            self.disable_all_items()
            self.stop()

    @property
    def chosen_stops(self) -> list[Stop]:
        return self._dropdown.chosen_stops(self._game)


class ActionChoice(View):

    def __init__(self, team: Team):
        self._dropdown = ActionDropdown(self, team.available_starting_actions)
        self._game = team._game
        # always do awo minute timeout...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    @property
    def chosen_action(self) -> Action | None:
        return self._dropdown.chosen_action(self._game)

    def update(self) -> None:
        if self._dropdown.chosen_action(self._game):
            self.disable_all_items()
            self.stop()


class CurseChoice(View):

    def __init__(self, team: Team):
        self._dropdown = ActionDropdown(self, [action for action in team.available_starting_actions
                                               if action.type == ActionType.CURSE])
        self._game = team._game
        # always do awo minute timeout...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    @property
    def chosen_curse(self) -> Action | None:
        return self._dropdown.chosen_action(self._game)

    def update(self) -> None:
        if self._dropdown.chosen_action(self._game):
            self.disable_all_items()
            self.stop()




class CounterChoice(View):

    def __init__(self, team: Team, action: Action):
        self._dropdown = ActionDropdown(self, team.counter_options(
            action), "Don't counter", f"Allow the {action.title} card to be played.")
        self._game = team._game
        # always do a two minute timeout...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    @property
    def chosen_counter(self) -> Action | None:
        return self._dropdown.chosen_action(self._game)

    def update(self) -> None:
        self.disable_all_items()
        self.stop()


class VictimChoice(View):

    def __init__(self, team: Team, allow_self: bool = False):
        self._dropdown = TeamDropdown(
            self, [other_team for other_team in team._game.all_teams if allow_self or not team == other_team])
        self._game = team._game
        # always do a two minute timeout...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    @property
    def chosen_victim(self) -> Team | None:
        return self._dropdown.chosen_team(self._game)

    def update(self) -> None:
        if self._dropdown.chosen_team(self._game):
            self.disable_all_items()
            self.stop()


class RevealSecretChoice(View):

    def __init__(self, team: Team):
        self._dropdown = StopDropdown(self, team.unrevealed_secrets, 1, 1)
        self._game = team._game
        self._team = team
        # allow 5 minutes to choose...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    def update(self) -> None:
        self.disable_all_items()
        self.stop()

    @property
    def chosen_secret(self) -> Stop:
        chosen_stop = self._dropdown.chosen_stop(self._game)
        if chosen_stop:
            return chosen_stop
        else:
            return choice(self._team.unrevealed_secrets)


class StealChoice(View):

    def __init__(self, victim: Team, allow_claimed: bool = False):
        self._dropdown = StopDropdown(
            self, victim.claimed_stops if allow_claimed else victim.claimed_unlocked_stops, 1, 1)
        self._game = victim._game
        # allow 5 minutes to choose...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    def update(self) -> None:
        self.disable_all_items()
        self.stop()

    @property
    def chosen_stop(self) -> Stop | None:
        return self._dropdown.chosen_stop(self._game)


class DonationChoice(View):

    def __init__(self, team: Team):
        count = len(team._game.all_teams) - 1
        self._dropdown = StopDropdown(self, team.secrets, count, count)
        self._game = team._game
        self._team = team
        # allow 2 minutes to choose...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    def update(self) -> None:
        if len(self._dropdown.chosen_stops(self._game)) == len(self._game.all_teams) - 1:
            self.disable_all_items()
            self.stop()

    @property
    def chosen_secrets(self) -> list[Stop]:
        if self._dropdown.chosen_stops(self._game):
            return self._dropdown.chosen_stops(self._game)
        else:
            # choose random ones instead
            return sample(self._team.secrets, k=2)


class DropSecretsChoice(View):

    def __init__(self, team: Team):
        count = 2
        self._dropdown = StopDropdown(self, team.secrets, count, count)
        self._game = team._game
        self._team = team
        # allow 2 minutes to choose...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)

    # update mulligan choices
    def update(self) -> None:
        if len(self._dropdown.chosen_stops(self._game)) == len(self._game.all_teams) - 1:
            self.disable_all_items()
            self.stop()

    @property
    def chosen_secrets(self) -> list[Stop]:
        if self._dropdown.chosen_stops(self._game):
            return self._dropdown.chosen_stops(self._game)
        else:
            # choose random ones instead
            return sample(self._team.secrets, k=2)


class ActionZoneChoice(View):

    def __init__(self, zones: list[Zone]):
        self._dropdown = ZoneDropdown(self, zones)
        # always do awo minute timeout...
        super().__init__(self._dropdown, timeout=120, disable_on_timeout=True)
        self._game = zones[0].game

    @property
    def chosen_zone(self) -> Zone | None:
        return self._dropdown.chosen_zone(self._game)

    def update(self) -> None:
        if self._dropdown.chosen_zone(self._game):
            self.disable_all_items()
            self.stop()


def truncate(text: str) -> str:
    return text if len(text) <= 100 else text[0:97] + '...'
