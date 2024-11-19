from discord import SlashCommandGroup, ApplicationContext, Interaction, Guild, slash_command, option, SlashCommandOptionType
from utils.data import game, team, mentionChat, channel_id, mention, getUpdatesChannel, mentionPossessive, countdownTo, exactTime
from utils.responses import complain, sendMessage
from utils.autocomplete import other_team_name
from utils.embeds import embed_available_starting_actions, embed_counter_options, embed_played_action, embed_available_actions, embed_revealed_secrets, embed_available_curses, embed_unrevealed_secrets, embed_unlocked_stops, embed_locked_lines
from utils.views import ActionChoice, CounterChoice, VictimChoice, RevealSecretChoice, StealChoice, CurseChoice
from utils.buttons import grid, actionPlayedRow, actionVictimRow, standardCheckRow, actionAnnouncementRow, stopActionsRow, seeChallengesRow, checkCursesRow
from tramopoly import Card, Team, Action, Announcement, ClearCurse, OngoingCurse, Interchange, Railroaded, TicketInspection, Derailment, Special, Curse, Stop, ActionType
from game import end_game
from asyncio import sleep
from datetime import datetime


@slash_command(description="Play any action card, except counter cards.")
async def play_action_card(ctx: ApplicationContext | Interaction):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only play action cards during a game.")
        return
    # make sure this is an active player
    role_team = team(ctx.user.top_role)
    if not role_team:
        await complain(ctx, "Not in a team", "You can only play action cards if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only play action cards in your team chat, {mentionChat(role_team)}.")
        return
    elif role_team.in_veto:
        await complain(ctx, "Cannot currently play action cards", f"You cannot play any non-counter cards until you have completed your veto period.")
        return
    elif not role_team.may_progress:
        await complain(ctx, "Cannot currently progress in game", f"You cannot play any non-counter cards until you clear any clearable curses.")
        return
    # check if any action cards available
    if not role_team.available_starting_actions:
        await complain(ctx, "No playable action cards", "You do not own any non-counter cards.")
        return
    # now make embed and ask for a choice
    action_choice = ActionChoice(role_team)
    await sendMessage(ctx, f"Choose an action card to play...", embed_available_starting_actions(role_team), view=action_choice)
    # wait for them to make a choice
    await action_choice.wait()
    await ctx.edit_original_response(view=action_choice)
    # make sure they actually chose one
    chosen_action = action_choice.chosen_action
    if not chosen_action:
        await complain(ctx.channel, "No action card chosen", f"You didn't choose an action card.")
        return
    # do itttt!
    await play_specific_action_card(ctx, chosen_action)


@slash_command(description="Play any action card, except counter cards.")
@option(name="victim", description="The name of the team whose hand you wish to see.", input_type=SlashCommandOptionType.string, autocomplete=other_team_name, required=True, parameter_name="victim_name")
async def play_curse(ctx: ApplicationContext | Interaction, victim_name: str):
    ctx = ctx.interaction if isinstance(ctx, ApplicationContext) else ctx
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx, "Not in a game", "You can only play curse cards during a game.")
        return
    # make sure this is an active player
    role_team = team(ctx.user.top_role)
    if not role_team:
        await complain(ctx, "Not in a team", "You can only play curse cards if you're part of a team.")
        return
    channel_team = team(ctx.channel)
    # make sure we're in the correct channel
    if role_team != channel_team:
        await complain(ctx, "Not in correct channel", f"You can only play curse cards in your team chat, {mentionChat(role_team)}.")
        return
    elif not role_team.may_progress:
        await complain(ctx, "Cannot currently progress in game", f"You cannot play any curse cards until you clear any clearable curses.")
        return
    # check if any action cards available
    if not role_team.available_curses:
        await complain(ctx, "No playable action cards", "You do not own any curse cards.")
        return
    # determine the victims
    chosen_victim = live_game.getTeamFromName(victim_name)
    if not chosen_victim:
        await complain(ctx, "Invalid team selection", "Try again with a correct team name.")
        return
    elif chosen_victim == role_team:
        await complain(ctx, "Invalid victim choice", "You can't curse yourself.")
        return
    # now make embed and ask for a choice
    curse_choice = CurseChoice(role_team)
    await sendMessage(ctx, f"Choose a curse card to play...", embed_available_curses(role_team), view=curse_choice)
    # wait for them to make a choice
    await curse_choice.wait()
    await ctx.edit_original_response(view=curse_choice)
    # make sure they actually chose one
    chosen_action = curse_choice.chosen_curse
    if not chosen_action:
        await complain(ctx.channel, "No curse card chosen", f"You didn't choose a curse card.")
        return
    # do itttt!
    await play_specific_action_card(ctx, chosen_action, chosen_victim)


async def play_specific_action_card(ctx: ApplicationContext | Interaction, action: Action, victim: Team | None = None, target: Stop | None = None):
    # check if live
    live_game = game(ctx.guild, True)
    if not live_game:
        await complain(ctx.channel, "Not in a game", "You can only play action cards during a game.")
        return
    # make sure this is an active player (WILL ALWAYS BE IN A VALID CHANNEL)
    channel_team = team(ctx.channel)
    if channel_team != action.owner:
        await complain(ctx.channel, "Not your action card", "You don't have this action card in your hand.")
        return
    elif channel_team.in_veto:
        await complain(ctx, "Cannot currently play action cards", f"You cannot play any non-counter cards until you have completed your veto period.")
        return
    elif not channel_team.may_progress:
        await complain(ctx, "Cannot currently progress in game", f"You cannot play any non-counter cards until you clear any clearable curses.")
        return
    if victim and not action.playableTeam(victim):
        await complain(ctx.channel, "Invalid victim choice", f"You can't play this action card against {victim.name}.")
        return
    # now do the specific action card!
    if action.code == "ANNOUNCEMENT":
        await playAnnouncement(action, ctx.guild, victim)
    elif action.code.startswith("CURSE-CLEAR"):
        await playClearCurse(action, ctx.guild, victim)
    elif action.code.startswith("CURSE-ONGOING"):
        await playOngoingCurse(action, ctx.guild, victim)
    elif action.code == "INTERCHANGE":
        await playInterchange(action, ctx.guild, victim, target)
    elif action.code == "RAILROADED":
        await playRailroaded(action, ctx.guild, victim, target)
    elif action.code == "TICKETINSPECTION":
        await playTicketInspection(action, ctx.guild, victim)
    elif action.code == "DERAILMENT":
        await playDerailment(action, ctx.guild, victim, target)
    else:
        print(f'NOT VALID CARD CODE: {action.code}')
        return
    # check if game over...
    if live_game.game_over:
        # do end of game
        await end_game(ctx.guild)


async def tryCounter(original_card: Action, card: Action, victim: Team, guild: Guild, *args: Card) -> bool:
    # tell playing team...\
    player = card.owner
    await sendMessage(guild.get_channel(channel_id(player)), f"Waiting for a response from {mention(victim, player, False)}...", embed_played_action(card, player, args))
    # tell victim
    counter_choice = CounterChoice(victim, card)
    message = await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player)} played their {card.title} card against {mention(victim, victim, False)}. Would you like to counter it?", embed_played_action(card, victim, args), embed_counter_options(victim, card), view=counter_choice)
    await counter_choice.wait()
    await message.edit(view=counter_choice)
    counter = counter_choice.chosen_counter
    if not counter:
        # expire existing counter
        card.expireCounter()
        return False
    success = counter.play(card)
    if success:
        return True
    # swap roles and try and counter the counter card!
    countered = await tryCounter(original_card, counter, player, victim, args)
    if countered:
        return False
    # YES IT HAS BEEN COUNTERED
    return True


async def tryReroute(curse: Action, victim: Team, guild: Guild) -> bool:
    # tell playing team...\
    player = curse.owner
    await sendMessage(guild.get_channel(channel_id(player)), f"Waiting for a response from {mention(victim, player, False)}...", embed_played_action(curse, player))
    # tell victim
    counter_choice = CounterChoice(victim, curse)
    message = await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player)} played their {curse.title} curse against {mention(victim, victim, False)}. Would you like to counter it?", embed_played_action(curse, victim), embed_counter_options(victim, curse), view=counter_choice)
    await counter_choice.wait()
    await message.edit(view=counter_choice)
    counter = counter_choice.chosen_counter
    if not counter:
        # expire existing counter
        curse.expireCounter()
        return False
    success = counter.play(curse)
    if success:
        return True
    # swap roles and try and counter the counter card!
    countered = await tryCounter(curse, counter, player, victim)
    if countered:
        return False
    # YES IT HAS BEEN COUNTERED
    return True


# create loads of special ones.... e.g. PLAY INTERCHANGE, PLAY CLEARING CURSE etc
# DO COUNTER LOOP.... (recursive btw)
async def playAnnouncement(card: Announcement, guild: Guild, victim: Team | None = None):
    # get victim
    player = card.owner
    if not victim:
        victim_choice = VictimChoice(player)
        message = await sendMessage(guild.get_channel(channel_id(player)), "Choose a team to reveal their action cards...", embed_played_action(card), view=victim_choice)
        # try play
        await victim_choice.wait()
        await message.edit(view=victim_choice)
        # make sure there was actually a choice made
        victim = victim_choice.chosen_victim
        if not victim:
            await complain(guild.get_channel(channel_id(player)), "No victim selected", "You didn't choose who to play this card against.")
            return
    # now make sure it hasn't been countered
    success = card.play(victim)
    if not success:
        countered = await tryCounter(card, card, victim, guild)
        if countered:
            # TELL EVERYONE EVERYTHING!
            await sendMessage(guild.get_channel(channel_id(player)), f"{mention(victim, player)} successfully countered your {card.title} card.", embed_played_action(card, player),
                              view=grid(
                                  actionVictimRow(victim, player, None)
            ))
            await sendMessage(guild.get_channel(channel_id(victim)), f"You successfully countered the {card.title} card played against you by {mention(player, victim, capitalise=False)}.", embed_played_action(card, victim),
                              view=grid(
                                  actionPlayedRow(victim, player)
            ))
            await sendMessage(getUpdatesChannel(guild), f"{mention(victim)} successfully countered the {card.title} card played against them by {mention(player, capitalise=False)}.", embed_played_action(card),
                              view=grid(
                                  actionAnnouncementRow(victim, player)
            ))
            return
        else:
            card.play(victim)
    # DON'T INSTEAD
    await sendMessage(guild.get_channel(channel_id(player)), f"You successfully played your {card.title} card against {mention(victim, player)}.", embed_played_action(card, player), embed_available_actions(victim, player),
                      view=grid(
                          actionPlayedRow(player, victim)
    ))
    await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player, victim, capitalise=False)} played their {card.title} card against you.", embed_played_action(card, victim),
                      view=grid(
                          actionVictimRow(player, victim, card)
    ))
    await sendMessage(getUpdatesChannel(guild), f"{mention(player)} just played their {card.title} card against {mention(victim, capitalise=False)}!", embed_played_action(card), embed_available_actions(victim),
                      view=grid(
                          actionAnnouncementRow(player, victim)
    ))


async def playTicketInspection(card: TicketInspection, guild: Guild, victim: Team | None = None):
    # get victim
    player = card.owner
    if not victim:
        victim_choice = VictimChoice(player)
        message = await sendMessage(guild.get_channel(channel_id(player)), "Choose a team to reveal one of their secret cards...", embed_played_action(card), view=victim_choice)
        # try play
        await victim_choice.wait()
        await message.edit(view=victim_choice)
        # make sure there was actually a choice made
        victim = victim_choice.chosen_victim
        if not victim:
            await complain(guild.get_channel(channel_id(player)), "No victim selected", "You didn't choose who to play this card against.")
            return
    # now make sure it hasn't been countered
    success = card.play(victim)
    if not success:
        countered = await tryCounter(card, card, victim, guild)
        if countered:
            # TELL EVERYONE EVERYTHING!
            await sendMessage(guild.get_channel(channel_id(player)), f"{mention(victim, player)} successfully countered your {card.title} card.", embed_played_action(card, player),
                              view=grid(
                                  actionVictimRow(victim, player, None)
            ))
            await sendMessage(guild.get_channel(channel_id(victim)), f"You successfully countered the {card.title} card played against you by {mention(player, victim, capitalise=False)}.", embed_played_action(card, victim),
                              view=grid(
                                  actionPlayedRow(victim, player)
            ))
            await sendMessage(getUpdatesChannel(guild), f"{mention(victim)} successfully countered the {card.title} card played against them by {mention(player, capitalise=False)}.", embed_played_action(card),
                              view=grid(
                                  actionAnnouncementRow(victim, player)
            ))
            return
    # now get secret choice....
    secret_choice = RevealSecretChoice(victim)
    message = await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player, victim, capitalise=False)} played their {card.title} card against you. Choose a secret to reveal...", embed_played_action(card, victim), embed_unrevealed_secrets(victim), view=secret_choice)
    await secret_choice.wait()
    await message.edit(view=secret_choice)
    # now reveal the secret (WILL BE RANDOM IF REQUIRED)
    victim.revealSecret(secret_choice.chosen_secret)
    # DON'T INSTEAD
    await sendMessage(guild.get_channel(channel_id(player)), f"You successfully played your {card.title} card against {mention(victim, player)}.", embed_played_action(card, player), embed_revealed_secrets(victim, player),
                      view=grid(
                          actionPlayedRow(player, victim)
    ))
    await sendMessage(getUpdatesChannel(guild), f"{mention(player)} just played their {card.title} card against {mention(victim, capitalise=False)}!", embed_played_action(card), embed_revealed_secrets(victim),
                      view=grid(
                          actionAnnouncementRow(player, victim)
    ))


async def playClearCurse(card: ClearCurse, guild: Guild, victim: Team | None = None):
    # get victim
    player = card.owner
    if not victim:
        victim_choice = VictimChoice(player)
        message = await sendMessage(guild.get_channel(channel_id(player)), "Which team would you like to curse...", embed_played_action(card), view=victim_choice)
        # try play
        await victim_choice.wait()
        await message.edit(view=victim_choice)
        # make sure there was actually a choice made
        victim = victim_choice.chosen_victim
        if not victim:
            await complain(guild.get_channel(channel_id(player)), "No team selected", "You didn't choose which team to curse.")
            return
    if not card.playableTeam(victim):
        await complain(guild.get_channel(channel_id(player)), "Action not possible", f"You can't play this curse againt {mention(victim, player, False)} right now as they have {Special("IMMUNITY").name}.")
        return
    # now make sure it hasn't been countered
    success = card.play(victim)
    if not success:
        rerouted = await tryCounter(card, card, victim, guild)
        if rerouted:
            # TELL EVERYONE EVERYTHING!
            await sendMessage(guild.get_channel(channel_id(player)), f"{mention(victim, player)} successfully rerouted your {card.title} curse. You must now suffer the curse! Any challenge you were completing has been paused. Once you clear your non-ongoing curses you can resume a previous challenge.", embed_played_action(card, player),
                              view=grid(
                                  actionVictimRow(victim, player, card)
            ))
            await sendMessage(guild.get_channel(channel_id(victim)), f"You successfully rerouted the {card.title} curse played against you by {mention(player, victim, capitalise=False)}. Now they must suffer the curse!", embed_played_action(card, victim),
                              view=grid(
                                  actionPlayedRow(victim, player)
            ))
            await sendMessage(getUpdatesChannel(guild), f"{mention(victim)} successfully rerouted the {card.title} curse played against them by {mention(player, capitalise=False)}!", embed_played_action(card),
                              view=grid(
                                  actionAnnouncementRow(victim, player)
            ))
            return
        else:
            card.play(victim)
    # DON'T INSTEAD
    await sendMessage(guild.get_channel(channel_id(player)), f"You successfully played your {card.title} curse against {mention(victim, player)}.", embed_played_action(card, player),
                      view=grid(
                          actionPlayedRow(player, victim)
    ))
    await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player, victim, capitalise=False)} played their {card.title} curse against you. Any challenge you were completing has been paused. Once you clear your non-ongoing curses you can resume a previous challenge.", embed_played_action(card, victim),
                      view=grid(
                          actionVictimRow(player, victim, card),
    ))
    await sendMessage(getUpdatesChannel(guild), f"{mention(player)} just played their {card.title} curse against {mention(victim, capitalise=False)}!", embed_played_action(card),
                      view=grid(
                          actionAnnouncementRow(player, victim)
    ))


async def playOngoingCurse(card: OngoingCurse, guild: Guild, victim: Team | None = None):
    # get victim
    player = card.owner
    if not victim:
        victim_choice = VictimChoice(player)
        message = await sendMessage(guild.get_channel(channel_id(player)), "Which team would you like to curse...", embed_played_action(card), view=victim_choice)
        # try play
        await victim_choice.wait()
        await message.edit(view=victim_choice)
        # make sure there was actually a choice made
        victim = victim_choice.chosen_victim
        if not victim:
            await complain(guild.get_channel(channel_id(player)), "No team selected", "You didn't choose which team to curse.")
            return
    if not card.playableTeam(victim):
        await complain(guild.get_channel(channel_id(player)), "Action not possible", f"You can't play this curse againt {mention(victim, player, False)} right now as they have Curse Immunity.")
        return
    # now make sure it hasn't been countered
    success = card.play(victim)
    if not success:
        rerouted = await tryReroute(card, victim, guild)
        if rerouted:
            # TELL EVERYONE EVERYTHING!
            await sendMessage(guild.get_channel(channel_id(player)), f"{mention(victim, player)} successfully rerouted your {card.title} curse. You must now suffer the curse! It will wear off {exactTime(card.getEndTime())} ({countdownTo(card.getEndTime())})", embed_played_action(card, player),
                              view=grid(
                                  actionVictimRow(victim, player, card)
            ))
            await sendMessage(guild.get_channel(channel_id(victim)), f"You successfully rerouted the {card.title} curse played against you by {mention(player, victim, capitalise=False)}. Now they must suffer the curse!", embed_played_action(card, victim),
                              view=grid(
                                  actionPlayedRow(victim, player)
            ))
            await sendMessage(getUpdatesChannel(guild), f"{mention(victim)} successfully rerouted the {card.title} curse played against them by {mention(player, capitalise=False)}!", embed_played_action(card),
                              view=grid(
                                  actionAnnouncementRow(victim, player)
            ))
            await notifyOngoingCurse(card, guild, player)
            return
        else:
            card.play(victim)
    # DON'T INSTEAD
    await sendMessage(guild.get_channel(channel_id(player)), f"You successfully played your {card.title} curse against {mention(victim, player)}.", embed_played_action(card, player),
                      view=grid(
                          actionPlayedRow(player, victim)
    ))
    await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player, victim, capitalise=False)} played their {card.title} curse against you. The curse will wear off {exactTime(card.getEndTime())} ({countdownTo(card.getEndTime())})", embed_played_action(card, victim),
                      view=grid(
                          actionVictimRow(player, victim, card)
    ))
    await sendMessage(getUpdatesChannel(guild), f"{mention(player)} just played their {card.title} curse against {mention(victim, capitalise=False)}!", embed_played_action(card),
                      view=grid(
                          actionAnnouncementRow(player, victim)
    ))
    await notifyOngoingCurse(card, guild, victim)


async def notifyOngoingCurse(curse: OngoingCurse, guild: Guild, victim: Team):
    # wait for the curse to wear off!
    await sleep((curse.getEndTime() - datetime.now()).total_seconds())
    # wait a bit more if too early
    while curse in victim.ongoing_curses:
        await sleep(1)
    # don't bother if game over
    if curse.game.game_over:
        return
    # now send announcements!
    await sendMessage(guild.get_channel(channel_id(victim)), f"The {curse.title} curse has expired! You no longer have to follow its instructions.", embed_played_action(curse, victim),
                      view=grid(
                          checkCursesRow(victim, victim)
    ))
    await sendMessage(getUpdatesChannel(guild), f"{mention(victim)} no longer have to suffer the effects of the {curse.title} curse, as it has expired!", embed_played_action(curse),
                      view=grid(
                          standardCheckRow(victim)
    ))


async def playInterchange(card: Interchange, guild: Guild, victim: Team | None = None, stop_to_take: Stop | None = None):
    # get victim
    player = card.owner
    if not victim:
        victim_choice = VictimChoice(player)
        message = await sendMessage(guild.get_channel(channel_id(player)), "Which team would you like to swap stops with...", embed_played_action(card), view=victim_choice)
        # try play
        await victim_choice.wait()
        await message.edit(view=victim_choice)
        # make sure there was actually a choice made
        victim = victim_choice.chosen_victim
        if not victim:
            await complain(guild.get_channel(channel_id(player)), "No victim selected", "You didn't choose who to play this card against.")
            return
    if not card.playableTeam(victim):
        await complain(guild.get_channel(channel_id(player)), "Action not possible", f"You can't play this card againt {mention(victim, player, False)} right now.")
        return
    # choose a stop to give...
    steal_choice = StealChoice(player)
    message = await sendMessage(guild.get_channel(channel_id(player)), f"Which stop would you like to give to {mention(victim, player, False)}...", embed_played_action(card), embed_unlocked_stops(player, player), view=steal_choice)
    # try play
    await steal_choice.wait()
    await message.edit(view=steal_choice)
    # make sure there was actually a choice made
    stop_to_give = steal_choice.chosen_stop
    if not stop_to_give:
        await complain(guild.get_channel(channel_id(player)), "No stop selected", f"You didn't choose which stop to give to {mention(victim, player, False)}.")
        return
    if not stop_to_take:
        # choose a stop to take...
        steal_choice = StealChoice(victim)
        message = await sendMessage(guild.get_channel(channel_id(player)), f"Which stop would you like to take from {mention(victim, player, False)}...", embed_played_action(card), embed_unlocked_stops(victim, player), view=steal_choice)
        # try play
        await steal_choice.wait()
        await message.edit(view=steal_choice)
        # make sure there was actually a choice made
        stop_to_take = steal_choice.chosen_stop
        if not stop_to_take:
            await complain(guild.get_channel(channel_id(player)), "No stop selected", f"You didn't choose which stop to take from {mention(victim, player, False)}.")
            return
    # now make sure it hasn't been countered
    success = card.play(stop_to_take, stop_to_give)
    if not success:
        countered = await tryCounter(card, card, victim, guild, stop_to_take, stop_to_give)
        if countered:
            # TELL EVERYONE EVERYTHING!
            await sendMessage(guild.get_channel(channel_id(player)), f"{mention(victim, player)} successfully countered your {card.title} card.", embed_played_action(card, player, (stop_to_take, stop_to_give)),
                              view=grid(
                                  actionVictimRow(
                                      victim, player, None, secret=stop_to_take in player.secrets),
                                  stopActionsRow(player, stop_to_take)
            ))
            await sendMessage(guild.get_channel(channel_id(victim)), f"You successfully countered the {card.title} card played against you by {mention(player, victim, capitalise=False)}.", embed_played_action(card, victim, (stop_to_take, stop_to_give)),
                              view=grid(
                                  actionPlayedRow(
                                      victim, player, secret=stop_to_take in victim.secrets)
            ))
            await sendMessage(getUpdatesChannel(guild), f"{mention(victim)} successfully countered the {card.title} card played against them by {mention(player, capitalise=False)}.", embed_played_action(card, args=(stop_to_take, stop_to_give)),
                              view=grid(
                                  actionAnnouncementRow(victim, player)
            ))
            return
        else:
            # replay the card (it will work this time)
            card.play(stop_to_take, stop_to_give)
    # DON'T INSTEAD
    await sendMessage(guild.get_channel(channel_id(player)), f"You successfully played your {card.title} card against {mention(victim, player)}.", embed_played_action(card, player, (stop_to_give, stop_to_take)),
                      view=grid(
                          actionPlayedRow(
                              player, victim, secret=stop_to_take in player.secrets)
    ))
    await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player, victim, capitalise=False)} played their {card.title} card against you.", embed_played_action(card, victim, (stop_to_give, stop_to_take)),
                      view=grid(
                          actionVictimRow(player, victim, card,
                                          secret=stop_to_take in victim.secrets),
                          stopActionsRow(victim, stop_to_take)
    ))
    await sendMessage(getUpdatesChannel(guild), f"{mention(player)} just played their {card.title} card against {mention(victim, capitalise=False)}!", embed_played_action(card, args=(stop_to_give, stop_to_take)),
                      view=grid(
                          actionAnnouncementRow(player, victim)
    ))


async def playRailroaded(card: Railroaded, guild: Guild, victim: Team | None = None, stop_to_take: Stop | None = None):
    # get victim
    player = card.owner
    if not victim:
        victim_choice = VictimChoice(player)
        message = await sendMessage(guild.get_channel(channel_id(player)), "Which team would you like to steal from...", embed_played_action(card), view=victim_choice)
        # try play
        await victim_choice.wait()
        await message.edit(view=victim_choice)
        # make sure there was actually a choice made
        victim = victim_choice.chosen_victim
        if not victim:
            await complain(guild.get_channel(channel_id(player)), "No victim selected", "You didn't choose who to play this card against.")
            return
    if not card.playableTeam(victim):
        await complain(guild.get_channel(channel_id(player)), "Action not possible", f"You can't play this card againt {mention(victim, player, False)} right now.")
        return
    if not stop_to_take:
        # choose a stop to take...
        steal_choice = StealChoice(victim)
        message = await sendMessage(guild.get_channel(channel_id(player)), f"Which stop would you like to steal from {mention(victim, player, False)}...", embed_played_action(card), embed_unlocked_stops(victim, player), view=steal_choice)
        # try play
        await steal_choice.wait()
        await message.edit(view=steal_choice)
        # make sure there was actually a choice made
        stop_to_take = steal_choice.chosen_stop
        if not stop_to_take:
            await complain(guild.get_channel(channel_id(player)), "No stop selected", f"You didn't choose which stop to steal from {mention(victim, player, False)}.")
            return
    # now make sure it hasn't been countered
    success = card.play(stop_to_take)
    if not success:
        countered = await tryCounter(card, card, victim, guild, stop_to_take)
        if countered:
            # TELL EVERYONE EVERYTHING!
            await sendMessage(guild.get_channel(channel_id(player)), f"{mention(victim, player)} successfully countered your {card.title} card.", embed_played_action(card, player, stop_to_take),
                              view=grid(
                                  actionVictimRow(
                                      victim, player, None, secret=stop_to_take in player.secrets),
                                  stopActionsRow(player, stop_to_take)
            ))
            await sendMessage(guild.get_channel(channel_id(victim)), f"You successfully countered the {card.title} card played against you by {mention(player, victim, capitalise=False)}.", embed_played_action(card, victim, stop_to_take),
                              view=grid(
                                  actionPlayedRow(
                                      victim, player, secret=stop_to_take in victim.secrets)
            ))
            await sendMessage(getUpdatesChannel(guild), f"{mention(victim)} successfully countered the {card.title} card played against them by {mention(player, capitalise=False)}.", embed_played_action(card, args=stop_to_take),
                              view=grid(
                                  actionAnnouncementRow(victim, player)
            ))
            return
        else:
            # replay the card (it will work this time)
            card.play(stop_to_take)
    # DON'T INSTEAD
    await sendMessage(guild.get_channel(channel_id(player)), f"You successfully played your {card.title} card against {mention(victim, player)}.", embed_played_action(card, player, stop_to_take),
                      view=grid(
                          actionPlayedRow(
                              player, victim, secret=stop_to_take in player.secrets)
    ))
    await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player, victim, capitalise=False)} played their {card.title} card against you.", embed_played_action(card, victim, stop_to_take),
                      view=grid(
                          actionVictimRow(player, victim, card,
                                          secret=stop_to_take in victim.secrets),
                          stopActionsRow(victim, stop_to_take)
    ))
    await sendMessage(getUpdatesChannel(guild), f"{mention(player)} just played their {card.title} card against {mention(victim, capitalise=False)}!", embed_played_action(card, args=stop_to_take),
                      view=grid(
                          actionAnnouncementRow(player, victim)
    ))


async def playDerailment(card: Derailment, guild: Guild, victim: Team | None = None, stop_to_unclaim: Stop | None = None):
    # get victim
    player = card.owner
    if not victim:
        victim_choice = VictimChoice(player, True)
        message = await sendMessage(guild.get_channel(channel_id(player)), "Which team's stop would you like to unclaim...", embed_played_action(card), view=victim_choice)
        # try play
        await victim_choice.wait()
        await message.edit(view=victim_choice)
        # make sure there was actually a choice made
        victim = victim_choice.chosen_victim
        if not victim:
            await complain(guild.get_channel(channel_id(player)), "No team selected", "You didn't choose whose stop to unclaim.")
            return
    if not card.playableTeam(victim):
        await complain(guild.get_channel(channel_id(player)), "Action not possible", f"You can't play this card againt {mention(victim, player, False)} right now.")
        return
    if not stop_to_unclaim:
        # choose a stop to take...
        steal_choice = StealChoice(victim, True)
        message = await sendMessage(guild.get_channel(channel_id(player)), f"Which stop would you like to unclaim from {mentionPossessive(victim, player, False)} hand...", embed_played_action(card), embed_unlocked_stops(victim, player), embed_locked_lines(victim, player), view=steal_choice)
        # try play
        await steal_choice.wait()
        await message.edit(view=steal_choice)
        # make sure there was actually a choice made
        stop_to_unclaim = steal_choice.chosen_stop
        if not stop_to_unclaim:
            await complain(guild.get_channel(channel_id(player)), "No stop selected", f"You didn't choose which stop to unclaim from {mentionPossessive(victim, player, False)} hand.")
            return
    # now make sure it hasn't been countered (WON'T BE COUNTERED BY SAME TEAM)
    success = card.play(stop_to_unclaim)
    if not success:
        countered = await tryCounter(card, card, victim, guild, stop_to_unclaim)
        if countered:
            # TELL EVERYONE EVERYTHING!
            await sendMessage(guild.get_channel(channel_id(player)), f"{mention(victim, player)} successfully countered your {card.title} card.", embed_played_action(card, player, stop_to_unclaim),
                              view=grid(
                                  actionVictimRow(
                                      victim, player, None, secret=stop_to_unclaim in player.secrets)
            ))
            await sendMessage(guild.get_channel(channel_id(victim)), f"You successfully countered the {card.title} card played against you by {mention(player, victim, capitalise=False)}.", embed_played_action(card, victim, stop_to_unclaim),
                              view=grid(
                                  actionPlayedRow(
                                      victim, player, secret=stop_to_unclaim in victim.secrets)
            ))
            await sendMessage(getUpdatesChannel(guild), f"{mention(victim)} successfully countered the {card.title} card played against them by {mention(player, capitalise=False)}.", embed_played_action(card, args=stop_to_unclaim),
                              view=grid(
                                  actionAnnouncementRow(victim, player)
            ))
            return
        else:
            # replay the card (it will work this time)
            card.play(stop_to_unclaim)
    # DON'T INSTEAD (also allow to see challenges because yay :D our turn now)
    await sendMessage(guild.get_channel(channel_id(player)), f"You successfully played your {card.title} card against {mention(victim, player, capitalise=False)}.", embed_played_action(card, player, stop_to_unclaim),
                      view=grid(
                          actionPlayedRow(
                              player, victim, secret=stop_to_unclaim in player.secrets),
                          seeChallengesRow(stop_to_unclaim)
    ))
    if victim != player:
        await sendMessage(guild.get_channel(channel_id(victim)), f"{mention(player, victim, capitalise=False)} played their {card.title} card against you.", embed_played_action(card, victim, stop_to_unclaim),
                          view=grid(
                              actionVictimRow(
                                  player, victim, card, secret=stop_to_unclaim in victim.secrets),
                              seeChallengesRow(stop_to_unclaim)
        ))
    await sendMessage(getUpdatesChannel(guild), f"{mention(player)} just played their {card.title} card against {mention(victim, capitalise=False)}!", embed_played_action(card, args=stop_to_unclaim),
                      view=grid(
                          actionAnnouncementRow(player, victim)
    ))
