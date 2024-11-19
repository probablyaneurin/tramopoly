from utils.data import game, getObserver, team
from utils.responses import complain, sendMessage
from utils.embeds import embed_stop, embed_line, embed_challenges, embed_unlocked_stops, embed_locked_lines, embed_available_actions, embed_secrets, embed_revealed_secrets, embed_curses, embed_abilities, embed_map
from discord import Interaction, SlashCommandGroup, option, SlashCommandOptionType, ApplicationContext, slash_command
from utils.autocomplete import stop_name, team_name
from utils.choices import LINES
from utils.buttons import grid, checkHandRow, claimableLinesRow, secretChallengesRow, checkSecretsRow, teamActionsRow, checkLineRow, checkStopRow, stopActionsRow, checkCursesRow, clearCursesRow, standardCheckRow, mapRow
import tramopoly

check = SlashCommandGroup("check")


@check.command(description="See any tram stop card, and related information.")
@option(name="name", description="The name of the tram stop card you wish to see.", input_type=SlashCommandOptionType.string, autocomplete=stop_name, required=True, parameter_name="search_term")
async def stop(ctx: ApplicationContext | Interaction, search_term: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild)
    observer = getObserver(ctx)
    if live_game:
        stop = live_game.searchStop(search_term)
    else:
        stop = tramopoly.searchStop(search_term)
    # make sure the stop is real
    if not stop:
        # send complaint
        await complain(ctx, "Invalid stop name.", "Try again with a correct tram stop name.")
        return
    # now delay
    await ctx.response.defer()
    # create embed
    if not live_game:
        # include challenges if the stop hasn't been claimed yet
        await sendMessage(ctx, None, embed_stop(stop, observer), embed_challenges(stop))
    elif not stop.claimed:
        await sendMessage(ctx, None, embed_stop(stop, observer), embed_challenges(stop),
                          view=grid(
                              checkStopRow(stop, observer),
                              stopActionsRow(observer, stop) if observer else None
        ))
    else:
        await sendMessage(ctx, None, embed_stop(stop, observer),
                          view=grid(
                              checkStopRow(stop, observer),
                              stopActionsRow(observer, stop) if observer else None
        ))


@check.command(description="See which stops are locked into any line during a game.")
@option(name="colour", description="The colour of the line you wish to see information about.", input_type=SlashCommandOptionType.string, choices=LINES, required=True, parameter_name="colour")
async def line(ctx: ApplicationContext | Interaction, colour: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only check the status of a line during a game.")
        return
    # NOW delay
    await ctx.response.defer()
    observer = getObserver(ctx)
    line = tramopoly.Line(colour, live_game)
    # create embed
    await sendMessage(ctx, None, embed_line(line, observer),
                      view=grid(
                          checkLineRow(line, observer)
    ))


@check.command(description="See any team's hand (claimed stops). You may only see your own action cards in your team chat.")
@option(name="team", description="The name of the team whose hand you wish to see.", input_type=SlashCommandOptionType.string, autocomplete=team_name, required=False, parameter_name="team_name")
async def hand(ctx: ApplicationContext | Interaction, team_name: str = ""):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only check a team's hand during a game.")
        return
    observer = getObserver(ctx)
    chosen_team = (live_game.getTeamFromName(team_name)
                   if team_name else team(ctx.user.top_role))
    if not chosen_team:
        await complain(ctx, "Invalid team selection", "Try again with a correct team name.")
        return
    # NOW delay
    await ctx.response.defer()
    # create embed (omit action cards for other teams)
    if chosen_team == observer:
        await sendMessage(ctx, None, embed_unlocked_stops(chosen_team, observer),
                          embed_locked_lines(chosen_team, observer),
                          embed_available_actions(chosen_team, observer),
                          view=grid(
                              checkHandRow(chosen_team, observer),
                              claimableLinesRow(chosen_team)
        ))
    else:
        await sendMessage(ctx, None, embed_unlocked_stops(chosen_team, observer),
                          embed_locked_lines(chosen_team, observer),
                          view=grid(
                              checkHandRow(chosen_team, observer),
                              teamActionsRow(observer, chosen_team)
        ))


@check.command(description="See any team's revealed secret cards. You may only see all your own secret cards in your team chat.")
@option(name="team", description="The name of the team whose secret cards you wish to see.",  input_type=SlashCommandOptionType.string, autocomplete=team_name, required=False, parameter_name="team_name")
async def secret_cards(ctx: ApplicationContext | Interaction, team_name: str = ""):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only check a team's revealed secrets during a game.")
        return
    observer = getObserver(ctx)
    chosen_team = (live_game.getTeamFromName(team_name)
                   if team_name else team(ctx.user.top_role))
    if not chosen_team:
        await complain(ctx, "Invalid team selection", "Try again with a correct team name.")
        return
    # NOW delay
    await ctx.response.defer()
    # create embed (omit action cards for other teams)
    if chosen_team == observer:
        await sendMessage(ctx, None, embed_secrets(chosen_team),
                          view=grid(
                              checkSecretsRow(chosen_team, observer),
                              secretChallengesRow(chosen_team, observer)

        ))
    else:
        await sendMessage(ctx, None, embed_revealed_secrets(chosen_team, observer),
                          view=grid(
                              checkSecretsRow(chosen_team, observer),
                              secretChallengesRow(chosen_team, observer)
        ))


@check.command(description="See any team's active curses.")
@option(name="team", description="The name of the team whose active curses you wish to see.",  input_type=SlashCommandOptionType.string, autocomplete=team_name, required=False, parameter_name="team_name")
async def active_curses(ctx: ApplicationContext | Interaction, team_name: str = ""):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only check a team's active curses during a game.")
        return
    observer = getObserver(ctx)
    chosen_team = (live_game.getTeamFromName(team_name)
                   if team_name else team(ctx.user.top_role))
    if not chosen_team:
        await complain(ctx, "Invalid team selection", "Try again with a correct team name.")
        return
    # NOW delay
    await ctx.response.defer()
    # create embed (omit action cards for other teams)
    if chosen_team == observer:
        await sendMessage(ctx, None, embed_curses(chosen_team, observer),
                          view=grid(
                              checkCursesRow(chosen_team, observer),
                              clearCursesRow(chosen_team)
        ))
    else:
        await sendMessage(ctx, None, embed_curses(chosen_team, observer),
                          view=grid(
                              checkCursesRow(chosen_team, observer)
        ))


@check.command(description="See any team's active special abilities.")
@option(name="team", description="The name of the team whose active special abilities you wish to see.", input_type=SlashCommandOptionType.string, autocomplete=team_name, required=False, parameter_name="team_name")
async def active_abilities(ctx: ApplicationContext | Interaction, team_name: str = ""):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only check a team's active special abilities during a game.")
        return
    observer = getObserver(ctx)
    chosen_team = (live_game.getTeamFromName(team_name)
                   if team_name else team(ctx.user.top_role))
    if not chosen_team:
        await complain(ctx, "Invalid team selection", "Try again with a correct team name.")
        return
    # NOW delay
    await ctx.response.defer()
    # create embed (omit action cards for other teams)
    await sendMessage(ctx, None, embed_abilities(chosen_team, observer),
                      view=grid(
                          standardCheckRow(chosen_team, observer)
                      ))

# MAP


@slash_command(description="See the current status of the map, or a blank map if not currently in a game.")
async def map(ctx: ApplicationContext | Interaction):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # delay
    await ctx.response.defer()
    # check if live
    live_game = game(ctx.guild)
    observer = getObserver(ctx)
    # create embed
    await sendMessage(ctx, None, embed_map(live_game, observer),
                      view=grid(
                          mapRow(observer)
                      ))
