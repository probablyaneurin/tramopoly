from discord import AutocompleteContext
from tramopoly import getAllStops, searchStop
from discord.utils import basic_autocomplete, AutocompleteFunc
from utils.data import team, game, getObserver

STOP_NAMES = [stop.name for stop in getAllStops()]

async def get_unclaimed_stop_names(ctx: AutocompleteContext) -> list[str]:
    # check if we're even in a game
    local_game = game(ctx.interaction.guild)
    if not local_game:
        return []
    # compile unclaimed stop names
    return [stop.name for stop in local_game.unclaimed_stops] 

async def get_challenge_names(ctx: AutocompleteContext) -> list[str]:
    try:
        stop = searchStop(ctx.options["stop"])
    except:
        return []
    if not stop:
        return []
    return [challenge.title for challenge in stop.challenges]

async def get_team_names(ctx: AutocompleteContext) -> list[str]:
    # check if we're even in a game
    local_game = game(ctx.interaction.guild)
    if not local_game:
        return []
    # compile team names
    return [team.name for team in local_game.all_teams]

async def get_other_team_names(ctx: AutocompleteContext) -> list[str]:
    # check if we're even in a game
    local_game = game(ctx.interaction.guild)
    if not local_game:
        return []
    # don't include the team playing the command
    local_team = team(ctx.interaction.channel)
    # compile team names
    return [team.name for team in local_team.other_teams]

async def get_uncleared_curse_names(ctx: AutocompleteContext) -> list[str]:
    # check if we're even in a game
    local_game = game(ctx.interaction.guild)
    if not local_game or local_game.game_over:
        return []
    # make sure you're in correct channel and are in a team
    local_team = getObserver(ctx.interaction)
    # compile team names
    return [curse.title for curse in local_team.uncleared_curses]    

stop_name = basic_autocomplete(STOP_NAMES)
unclaimed_stop_name = basic_autocomplete(get_unclaimed_stop_names)
challenge_name = basic_autocomplete(get_challenge_names)
team_name = basic_autocomplete(get_team_names)
other_team_name = basic_autocomplete(get_other_team_names)
uncleared_curse_name = basic_autocomplete(get_uncleared_curse_names)