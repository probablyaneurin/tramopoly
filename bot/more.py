from utils.data import game, getObserver, team, mentionChat, mention, getUpdatesChannel, getEvidenceChannel
from utils.responses import complain, sendMessage
from utils.embeds import embed_line, embed_map, embed_locked_lines, embed_line_claim_options, embed_line, embed_locked_lines, embed_action, embed_curses
from discord import Interaction, option, SlashCommandOptionType, ApplicationContext, slash_command
from utils.choices import LINES
from utils.autocomplete import uncleared_curse_name
from utils.views import LineClaimChoice
from utils.buttons import grid, standardCheckRow, claimAnnouncementRow, curseClearedRow
from game import end_game


# CLAIM LINE
@slash_command(description="Claim a line by locking 3 stops into it, usually from 3 different zones.")
@option(name="colour", description="The colour of the line you wish to claim.", input_type=SlashCommandOptionType.string, choices=LINES, required=True, parameter_name="colour")
async def claim_line(ctx: ApplicationContext | Interaction, colour: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only claim lines during a game.")
        return
    # make sure this is an active player
    role_team = team(ctx.user.top_role)
    if not role_team:
        await complain(ctx, "Not in a team", "You can only claim lines if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only claim lines in your team chat, {mentionChat(role_team)}.")
        return
    # check if line claimable
    line = live_game.getLineFromColour(colour)
    # make sure it hasn't already been claimed
    if line.claimed:
        await complain(ctx, "Line already claimed", f"You cannot claim the {line.colour} line as it is already owned by {mention(line.owner, role_team, False)}.")
        return
    elif not line.is_claimable(role_team):
        await complain(ctx, "Line not claimable", f"You do not have the unlocked stops required to claim the {line.colour} line.")
        return
    # give them a choice
    stop_choice = LineClaimChoice(role_team, line)
    await sendMessage(ctx, f"Choose three stops to claim the {line.colour} line...", embed_line_claim_options(role_team, line), view=stop_choice)
    # wait for them to make a choice
    await stop_choice.wait()
    await ctx.edit_original_response(view=stop_choice)
    # determine what they chose
    stops = stop_choice.chosen_stops
    if not stops:
        await complain(stop_choice._dropdown._interaction, "No stops chosen", f"You didn't choose any stops.")
        return
    elif not line.is_valid_claim(stops):
        await complain(stop_choice._dropdown._interaction, "Invalid stop choices", f"The stops you chose do not cover enough zones to claim the {line.colour} line.")
        return
    # now claim the line!
    line.claim(stops)
    # now update them...
    await sendMessage(ctx.channel, f"{mention(role_team, role_team)} just claimed the {line.colour} line!", embed_line(line, role_team),
                      view=grid(
                          standardCheckRow(role_team, role_team)
    ))
    # and the main channel...
    await sendMessage(getUpdatesChannel(ctx.guild),
                      f"{mention(role_team)} just claimed the {
        line.colour} line!", embed_line(line),
        view=grid(
                          claimAnnouncementRow(role_team)
    ))
    # check if game over...
    if live_game.game_over:
        # do end of game
        await end_game(ctx.guild)
        return
    # check if has three lines but not won
    elif len(role_team.claimed_lines) >= 3:
        await sendMessage(getUpdatesChannel(ctx.guild),
                          f"{mention(role_team)} has claimed {len(
                              role_team.claimed_lines)} lines, but they don't yet own all their secret cards.", embed_locked_lines(role_team),
                          claimAnnouncementRow(role_team))

# CLEAR CURSE


@slash_command(description="When you complete a curse, clear it so you can play action cards and complete challenges again.")
@option(name="name", description="The name of the curse you wish to clear.", input_type=SlashCommandOptionType.string, autocomplete=uncleared_curse_name, required=True, parameter_name="curse_name")
async def clear_curse(ctx: ApplicationContext | Interaction, curse_name: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only clear curses during a game.")
        return
    # make sure this is an active player
    role_team = team(ctx.user.top_role)
    if not role_team:
        await complain(ctx, "Not in a team", "You can only clear curses if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only clear curses in your team chat, {mentionChat(role_team)}.")
        return
    # make sure curse exists
    curse = role_team.getClearableCurseByName(curse_name)
    if not curse:
        await complain(ctx, "Invalid curse name", f"You don't have any clearable curses with that name.")
        return
    # now defer
    await ctx.response.defer()
    # clear the curse
    role_team.clearCurse(curse)
    # show curses
    await sendMessage(ctx, f"{mention(role_team, role_team, True, False)} just cleared the {curse.title} curse. Upload relevant evidence in <#{getEvidenceChannel(ctx.guild).id}>.", embed_action(curse), embed_curses(role_team, role_team),
                      view=grid(
                          curseClearedRow(role_team)
    ))
    # and an announcement
    await sendMessage(
        getUpdatesChannel(ctx.guild),
        f"{mention(role_team)} just cleared the {
            curse.title} curse.", embed_action(curse),
        view=grid(
            standardCheckRow(role_team)
        ))
