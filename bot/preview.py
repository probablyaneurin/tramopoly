from utils.responses import complain, sendMessage
from utils.embeds import embed_challenges, embed_action, embed_special, embed_deck
from discord import Interaction, SlashCommandGroup, option, SlashCommandOptionType, ApplicationContext
from utils.autocomplete import stop_name
from utils.buttons import grid, previewChallengeRow
from utils.data import getObserver, game
from utils.choices import STANDARD_ACTIONS, CURSES, SPECIAL_ABILITIES, ZONES
import tramopoly
from tramopoly import Zone

preview = SlashCommandGroup("preview")


@preview.command(description="Preview the challenges available to complete at any tram stop.")
@option(name="stop", description="The name of the tram stop whose challenges you wish to see.",  input_type=SlashCommandOptionType.string, autocomplete=stop_name, required=True, parameter_name="stop_search_term")
async def challenges(ctx: ApplicationContext | Interaction, stop_search_term: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # we do not care about anything
    live_game = game(ctx.guild, allow_game_over=True)
    if live_game:
        chosen_stop = live_game.searchStop(stop_search_term)
    else:
        chosen_stop = tramopoly.searchStop(stop_search_term)
    # make sure the stop is real
    if not chosen_stop:
        # send complaint
        await complain(ctx, "Invalid stop name.", "Try again with a correct tram stop name.")
        return
    # now delay
    await ctx.response.defer()
    # create embed
    await sendMessage(ctx, None, embed_challenges(chosen_stop),
                      view=grid(
                          previewChallengeRow(chosen_stop, getObserver(ctx)
    )))


@preview.command(description="Preview any action card, excluding curses. (use /show curse_card)")
@option(name="name", description="The name of the action card you wish to see", input_type=SlashCommandOptionType.string, choices=STANDARD_ACTIONS, required=True, parameter_name="code")
async def action_card(ctx: ApplicationContext | Interaction, code: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # delay
    await ctx.response.defer()
    # we do not care about anything
    action = tramopoly.Action.load(code)
    # create embed
    await sendMessage(ctx, None, embed_action(action))


@preview.command(description="Preview any curse card.")
@option(name="name", description="The name of the curse card you wish to see", input_type=SlashCommandOptionType.string, choices=CURSES, required=True, parameter_name="code")
async def curse_card(ctx: ApplicationContext | Interaction, code: str):
    await action_card(ctx, code)


@preview.command(description="Preview any special ability.")
@option(name="name", description="The name of the special ability you wish to see.", input_type=SlashCommandOptionType.string, choices=SPECIAL_ABILITIES, required=True, parameter_name="code")
async def special_ability(ctx: ApplicationContext | Interaction, code: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # delay
    await ctx.response.defer()
    # we do not care about anything
    action = tramopoly.Special(code)
    # create embed
    await sendMessage(ctx, None, embed_special(action))


@preview.command(description="See the cards in any starting zone deck.")
@option(name="zone", decription="The zone deck you wish to see.", input_type=SlashCommandOptionType.integer, choices=ZONES, required=True, parameter_name="zone_number")
async def deck(ctx: ApplicationContext | Interaction, zone_number: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # delay
    await ctx.response.defer()
    # we do not care about anything
    zone = Zone(zone_number)
    # create embed
    await sendMessage(ctx, None, embed_deck(zone))

