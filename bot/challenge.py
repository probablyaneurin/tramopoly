from discord.ui.item import Item
from utils.data import game, team, mentionChat, countdownTo, mention, getUpdatesChannel, submitSelfie, getEvidenceChannel, channel_id, exactTime
from utils.responses import complain, sendMessage
from utils.embeds import embed_current_challenge, embed_claim, embed_selfie, embed_secrets, embed_discarded_secrets, embed_challenges
from discord import Interaction, SlashCommandGroup, option, SlashCommandOptionType, Attachment, ApplicationContext, Guild
from discord.ui import Select, View
from utils.autocomplete import challenge_name, unclaimed_stop_name
from tramopoly import Special, Action, Team
from datetime import datetime
from asyncio import sleep
from random import choice
from utils.views import RewardChoice, DonationChoice, DropSecretsChoice
from game import end_game
from utils.buttons import grid, currentChallengeRow, completedChallengeRow, claimableLinesRow, claimAnnouncementRow, seeChallengesRow, vetoedChallengeRow, standardCheckRow, previewChallengeRow

challenge = SlashCommandGroup("challenge")


@challenge.command(description="Start a challenge. You cannot attempt multiple challenges at once.")
@option(name="stop", description="Your current location. You must be standing on the tram platform when using this command.", input_type=SlashCommandOptionType.string, autocomplete=unclaimed_stop_name, required=True, parameter_name="stop_search_term")
@option(name="challenge", description="The name of the challenge you wish to begin.", input_type=SlashCommandOptionType.string, autocomplete=challenge_name, required=True, parameter_name="challenge_name")
@option(name="selfie", description="A selfie of the entire team on the tram platform. The stop's name must be clearly visible.", input_type=SlashCommandOptionType.attachment, required=True, parameter_name="selfie")
async def start(ctx: ApplicationContext | Interaction, stop_search_term: str, challenge_name: str, selfie: Attachment):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only start challenges during a game.")
        return
    role_team = team(ctx.user.top_role)
    # make sure this is an active player
    if not role_team:
        await complain(ctx, "Not in a team", "You can only start challenges if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only start challenges in your team chat, {mentionChat(role_team)}.")
        return
    elif role_team.in_veto:
        await complain(ctx, "Currently in veto period", f"You cannot start challenges until your veto period ends {countdownTo(role_team.veto_end)}.")
        return
    elif role_team.in_challenge:
        await complain(ctx, "Currently completing another challenge", f"You cannot start another challenge until you complete or veto {role_team.current_challenge.title} at {role_team.current_challenge_location.name}.")
        return
    elif not role_team.may_progress:
        await complain(ctx, "Cannot currently progress in game", f"You cannot start another challenge until you clear any clearable curses.")
        return
    # make sure it's a valid stop
    stop = live_game.searchStop(stop_search_term)
    # make sure the stop is real
    if not stop:
        # send complaint
        await complain(ctx, "Invalid stop name.", "Try again with a correct tram stop name.")
        return
    # make sure it's not already owned
    elif stop.claimed:
        # send complaint
        await complain(ctx, "Already owned stop.", f"{stop.name} is currently owned by {mention(stop.owner, role_team, False)}. Try again with an unclaimed stop.")
        return
    # make sure it's a valid challenge
    challenge = stop.getChallengeFromName(challenge_name)
    # make sure the challenge is real
    if not challenge:
        # send complaint
        await complain(ctx, "Invalid challenge name.", f"Try again with a correct challenge name at {stop.name}.")
        return
    # now delay
    if not ctx.response.is_done():  
        await ctx.response.defer()
    # save the selfie
    await submitSelfie(role_team, challenge, selfie)
    # officially start the challenge
    role_team.startChallenge(challenge)
    # create embed
    await sendMessage(ctx, None, embed_current_challenge(role_team),
                      view=grid(
                          currentChallengeRow(role_team)
    ))


@challenge.command(description="Show the challenge you're currently attempting, or how long is left in your veto period.")
async def current(ctx: ApplicationContext | Interaction):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only check your current challenge during a game.")
        return
    # make sure this is an active player
    role_team = team(ctx.user.top_role)
    if not role_team:
        await complain(ctx, "Not in a team", "You can only check your current challenge if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only check your current challenge in your team chat, {mentionChat(role_team)}.")
        return
    # now postpone
    await ctx.response.defer()
    # create embed
    await sendMessage(ctx, None, embed_current_challenge(role_team),
                      view=grid(
                          currentChallengeRow(role_team)
    ))


@challenge.command(description="When you successfully complete a challenge, add it to your hand and any rewards.")
async def complete(ctx: ApplicationContext | Interaction):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only complete challenges during a game.")
        return
    # make sure this is an active player
    role_team = team(ctx.user.top_role)
    if not role_team:
        await complain(ctx, "Not in a team", "You can only complete challenges if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only complete challenges in your team chat, {mentionChat(role_team)}.")
        return
    # and that we're currently doing a challenge
    elif role_team.in_veto or not role_team.in_challenge:
        await complain(ctx, "Not currently in a challenge", "You must first start a challenge using the </challenge start:1272138361980588053> command.")
        return
    # now postpone
    await ctx.response.defer()
    # complete the challenge
    challenge = role_team.current_challenge
    stop = challenge.location
    result = role_team.completeChallenge()
    # immediately send a message to the main channel INCLUDING SELFIE LOL
    await sendMessage(getUpdatesChannel(ctx.guild),
                      f"{mention(role_team)} just claimed {stop.name} by completing {
        challenge.title}!", embed_claim(stop, result if isinstance(result, Special) else None),
        embed_selfie(role_team, challenge),
        view=grid(
            claimAnnouncementRow(role_team),
            seeChallengesRow(stop)
    ))
    # check if they have a choice, if not just complete this nonsense
    # TODO: DONATION ABILITY
    if (not isinstance(result, list)) or live_game.game_over:
        # create dropdown
        await sendMessage(ctx, f"{mention(role_team, role_team)} just claimed {stop.name} by completing {challenge.title}! Upload relevant evidence in <#{getEvidenceChannel(ctx.guild).id}>.", embed_claim(stop, result, role_team),
                          view=grid(
                              completedChallengeRow(role_team, result, secret=stop in role_team.secrets),
                              claimableLinesRow(role_team),
        ))
        # now actually end the game if relevant
        if live_game.game_over:
            await end_game(ctx.guild)
        elif isinstance(result, Special):
            await completeSpecial(role_team, ctx.guild, result)
        return
    reward_choice = RewardChoice(result)
    await sendMessage(ctx, f"{mention(role_team, role_team)} just claimed {stop.name} by completing {challenge.title}! {mention(role_team, role_team)} must now choose a reward card as you have the {Special("REWARDCHOICE").name} special ability...", embed_claim(stop, result, role_team), view=reward_choice)
    # wait for timeout or choice made
    await reward_choice.wait()
    await ctx.edit_original_message(view=reward_choice)
    chosen = reward_choice.chosen_reward
    # choose a random one by default
    if not chosen:
        chosen = choice(result)
    # lock in action (will un-reserve the other one)
    chosen.choose()
    # now send the update
    await sendMessage(ctx, f"{mention(role_team, role_team)} just chose an action card. Upload relevant evidence for the challenge in <#{getEvidenceChannel(ctx.guild).id}>.", embed_claim(stop, chosen, role_team),
                      view=grid(
                          completedChallengeRow(role_team, result, secret=stop in role_team.secrets),
                          claimableLinesRow(role_team)
    ))


@challenge.command(description="If you choose to stop a challenge, veto it to take an 8 minute penalty.")
async def veto(ctx: ApplicationContext | Interaction):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only veto challenges during a game.")
        return
    # make sure this is an active player
    role_team = team(ctx.user.top_role)
    if not role_team:
        await complain(ctx, "Not in a team", "You can only veto challenges if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only veto challenges in your team chat, {mentionChat(role_team)}.")
        return
    # and that we're currently doing a challenge
    elif role_team.in_veto:
        await complain(ctx, "Already in a veto period", f"You can start another challenge when the veto ends {countdownTo(role_team.veto_end)}.")
        return
    elif not role_team.in_challenge:
        await complain(ctx, "Not currently in a challenge", "You must first start a challenge using the </challenge start:1272138361980588053> command.")
        return
    # now postpone
    await ctx.response.defer()
    # veto challenge
    stop = role_team.current_challenge_location
    role_team.vetoChallenge()
    # show embed
    await sendMessage(ctx, None, embed_current_challenge(role_team), view=grid(
        vetoedChallengeRow(role_team)
    ))
    await sleep((role_team.veto_end - datetime.now()).total_seconds())
    # now should be done! (sleep if not yet)
    while role_team.in_veto:
        await sleep(1)
    if live_game.game_over:
        return
    # now announce!
    await sendMessage(ctx, f"Your veto period has expired! If you're back on the tram stop platform, you may start a new challenge.", embed_challenges(stop), view=grid(
        previewChallengeRow(stop, role_team)
    ))


@challenge.command(description="If you've cleared all your non-ongoing curses, you can resume the previous challenge from anywhere.")
async def resume(ctx: ApplicationContext | Interaction):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only resume challenges during a game.")
        return
    # make sure this is an active player
    role_team = team(ctx.user.top_role)
    if not role_team:
        await complain(ctx, "Not in a team", "You can only resume challenges if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only resume challenges in your team chat, {mentionChat(role_team)}.")
        return
    # and that we're currently doing a challenge
    elif not role_team.paused_challenge:
        await complain(ctx, "No paused challenge", "You can start new challenges using the </challenge start:1272138361980588053> command.")
        return
    # now postpone
    await ctx.response.defer()
    # resume the challenge
    role_team.resumeChallenge()
    # create embed
    await sendMessage(ctx, None, embed_current_challenge(role_team),
                      view=grid(
                          currentChallengeRow(role_team)
    ))


async def completeSpecial(team: Team, guild: Guild, special: Special):
    if special.code == "DONATION":
        await doDonationAbility(team, guild)
    elif special.code == "DROPSECRETS":
        await doDropSecretsAbility(team, guild)
    elif special.code == "ADDSECRETS":
        await doAddSecretsAbility(team, guild)


async def doDonationAbility(team: Team, guild: Guild):
    # get them to choose stops, OTHERWISE RANDOM TWO
    donation_choice = DonationChoice(team)
    # now send stuff to the channel
    message = await sendMessage(guild.get_channel(channel_id(team)), f"Choose {len(team._game.all_teams)-1} secret cards to randomly donate to the other teams...", embed_secrets(team), view=donation_choice)
    # wait for choice and disable choosing thingy
    await donation_choice.wait()
    await message.edit(view=donation_choice)
    # check choice exists (WILL BE RANDOM IF NOT)
    chosen_secrets = donation_choice.chosen_secrets
    # actually do the donation
    team.doDonation(chosen_secrets)
    message = await sendMessage(guild.get_channel(channel_id(team)), f"You completed the {Special("DONATION").name} special ability, leaving you with just {len(team.secrets)} secret card(s).", embed_secrets(team),
                                view=grid(
                                    standardCheckRow(team, team)
    ))
    # send updates to the other teams...
    for other_team in team.other_teams:
        channel = guild.get_channel(channel_id(other_team))
        # send update message
        await sendMessage(channel, f"You've been donated an extra secret card from {mention(team, other_team, capitalise=False)} using the {Special("DONATION").name} special ability!", embed_secrets(other_team),
                          view=grid(
                              standardCheckRow(team, other_team)
        ))
    # now actually end the game if relevant
    if game(guild).game_over:
        await end_game(guild)


async def doDropSecretsAbility(team: Team, guild: Guild):
    # get them to choose stops, OTHERWISE RANDOM TWO
    drop_choice = DropSecretsChoice(team)
    # now send stuff to the channel
    message = await sendMessage(guild.get_channel(channel_id(team)), f"Choose 2 secret cards to discard...", embed_secrets(team), view=drop_choice)
    # wait for choice and disable choosing thingy
    await drop_choice.wait()
    await message.edit(view=drop_choice)
    # check choice exists (WILL BE RANDOM IF NOT)
    chosen_secrets = drop_choice.chosen_secrets
    # actually do the drop
    team.doDropSecrets(chosen_secrets)
    message = await sendMessage(guild.get_channel(channel_id(team)), f"You completed the {Special("DROPSECRETS").name} special ability, leaving you with just {len(team.secrets)} secret card(s).", embed_secrets(team),
                                view=grid(
                                    standardCheckRow(team, team)
    ))
    # send announcement to the main channel...
    await sendMessage(getUpdatesChannel(guild), f"{mention(team, capitalise=True)} just used their {Special("DROPSECRETS").name} to discard these two secrets!", embed_discarded_secrets(team, chosen_secrets),
                      view=grid(
                          standardCheckRow(team)
                      ))
    # now actually end the game if relevant
    if game(guild).game_over:
        await end_game(guild)


async def doAddSecretsAbility(team: Team, guild: Guild):
    # actually do the giving of secrets
    team.doAddSecrets()
    # send updates to the other teams...
    for other_team in team.other_teams:
        channel = guild.get_channel(channel_id(other_team))
        # send update message
        await sendMessage(channel, f"You've been dealt an extra **Zone 2** secret card, because {mention(team, other_team, capitalise=False)} activated the {Special("ADDSECRETS").name} special ability!", embed_secrets(other_team),
                          view=grid(
                              standardCheckRow(other_team, other_team)
                          ))
    # now actually end the game if relevant
    if game(guild).game_over:
        await end_game(guild)
