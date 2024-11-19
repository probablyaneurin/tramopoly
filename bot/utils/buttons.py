from discord.ui import View, Button
from discord import MISSING, ButtonStyle, Emoji, Interaction, PartialEmoji, Message
from utils.data import channel_id, role_id, team, mention, game, mentionPossessive, getEmojiCode, countdownTo, getObserver
from utils.embeds import embed_map, embed_unlocked_stops, embed_stop, embed_secrets, embed_revealed_secrets, embed_locked_lines, embed_available_actions, embed_challenges, embed_zone_options
from utils.responses import sendMessage, complain
from utils.views import ActionZoneChoice
from tramopoly import Team, Challenge, Action, Special, Stop, Line, ClearCurse, ActionType, Derailment

# generate button (args)
# can result in none if button not applicable to context

# this one ALWAYS EXISTS


def standardCheckRow(team: Team, observer: Team | None = None) -> list[Button]:
    row = [
        MapButton()
    ]
    # check your own hand
    if observer and team != observer:
        row.insert(0, CheckHandButton(observer, observer))
    # check the concerned team's hand
    if team:
        row.insert(0, CheckHandButton(team, observer))
    # lol return it
    return row


def currentChallengeRow(team: Team) -> list[Button]:
    if team.in_veto:
        return vetoedChallengeRow(team)
    elif team.in_challenge:
        return [
            CompleteChallengeButton(team),
            VetoChallengeButton(team)
        ]
    else:
        return [SearchStopButton()] + standardCheckRow(team, team)


def completedChallengeRow(team: Team, reward: Action | Special | None, secret: bool = False) -> list[Button]:
    row = standardCheckRow(team, team)
    # make sure you can actually play the action card!
    row.insert(0, SearchStopButton(True))
    if isinstance(reward, Action) and reward in team.available_starting_actions:
        row.insert(0, PlaySpecificActionButton(reward))
    if secret:
        row.insert(0, CheckSecretsButton(team, team))
    return row


def claimAnnouncementRow(owner: Team) -> list[Button]:
    return standardCheckRow(owner)


def vetoedChallengeRow(team: Team) -> list[Button]:
    return [SeeChallengesButton(team.current_challenge.location), SearchStopButton(True)] + standardCheckRow(team, team)


def curseClearedRow(team: Team) -> list[Button]:
    # TODO: add check curses
    row = standardCheckRow(team, team)
    if team.paused_challenge:
        row.insert(0, ResumeChallengeButton(team))
    return row


def actionPlayedRow(team: Team, victim: Team, secret: bool = False) -> list[Button]:
    row = standardCheckRow(team, team)
    row.insert(0, SearchStopButton())
    if victim != team:
        row.insert(1, CheckHandButton(victim, team))
    if secret:
        row.insert(0, CheckSecretsButton(team, team))
    return row


def actionVictimRow(team: Team, victim: Team, action: Action, secret: bool = False) -> list[Button]:
    row = standardCheckRow(team, victim)
    if isinstance(action, ClearCurse):
        row.insert(0, ClearCurseButton(action))
    if secret:
        row.insert(0, CheckSecretsButton(victim, victim))
    return row


def actionAnnouncementRow(team: Team, victim: Team) -> list[Button]:
    row = [
        CheckHandButton(team),
        MapButton()
    ]
    if victim != team:
        row.insert(1, CheckHandButton(victim))
    return row


def previewChallengeRow(stop: Stop, observer: Team | None = None) -> list[Button]:
    row = []
    if stop.game and (stop.game.in_progress or stop.game.game_over):
        row.append(MapButton())
    if observer:
        row.insert(0, SearchStopButton(True))
    if observer and stop.game and not stop.claimed and stop.game.in_progress:
        row = [StartChallengeButton(challenge, i, observer)
               for i, challenge in enumerate(stop.challenges)] + row
    return row


def checkHandRow(team: Team, observer: Team | None = None) -> list[Button]:
    row = [
        MapButton()
    ]
    if observer:
        row.insert(0, SearchStopButton())
    # looking at one's own hand
    if observer and not team.game.game_over and observer == team and team.available_starting_actions:
        row.insert(0, PlayAnyActionButton(observer))
    # looking at someone else's hand
    if observer and team != observer:
        row.insert(0, CheckHandButton(observer, observer))
    elif observer and team == observer:
        if team.secrets:
            row.insert(0, CheckSecretsButton(team, observer))
        if team.uncleared_curses or team.ongoing_curses:
            row.insert(0, CheckCursesButton(team, observer))
    #separate thing..
    if team != observer and team.revealed_secrets:
        row.insert(0, CheckSecretsButton(team, observer))
    # done!
    return row


def checkLineRow(line: Line, observer: Team | None = None) -> list[Button]:
    row = standardCheckRow(observer, observer)
    if observer:
        row.insert(0, SearchStopButton())
    if observer and not line.game.game_over and line.is_claimable(observer):
        row.insert(0, ClaimLineButton(line))
    # someone else has claimed the line
    elif line.claimed and line.owner != observer:
        row.insert(0, CheckHandButton(line.owner, observer))


def claimableLinesRow(team: Team) -> list[Button]:
    return [
        ClaimLineButton(line) for line in team.claimable_lines
    ]


def checkStopRow(stop: Stop, observer: Team | None = None) -> list[Button]:
    row = standardCheckRow(observer, observer)
    # someone else has claimed the line
    row.insert(0, SearchStopButton(True))
    if stop.claimed and stop.owner != observer:
        row.insert(0, CheckHandButton(stop.owner, observer))
    # also allow see challenges button if claimed
    if stop.claimed:
        row.insert(0, SeeChallengesButton(stop))
        if stop.locked:
            row.insert(0, CheckLineButton(stop.locked_line))
    # add challenge start buttons
    
    if observer and stop.game and not stop.claimed and stop.game.in_progress:
        row = [StartChallengeButton(challenge, i, observer)
               for i, challenge in enumerate(stop.challenges)] + row
    # done!
    return row


def checkCursesRow(team: Team, observer: Team | None = None) -> list[Button]:
    # TODO: add check timers feature
    row = standardCheckRow(team, observer)
    # TIMERS TO GO HERE

    return row


def clearCursesRow(team: Team) -> list[Button]:
    return [
        ClearCurseButton(curse) for curse in team.uncleared_curses
    ]


def checkSecretsRow(team: Team, observer: Team | None = None) -> list[Button]:
    row = standardCheckRow(team, observer)
    if observer:
        row.insert(0, SearchStopButton())
    return row


def secretChallengesRow(team: Team, observer: Team | None = None) -> list[Button]:
    if team == observer:
        return [
            SeeChallengesButton(secret, True) for secret in sorted(team.secrets)
            if not secret.claimed or secret.owner != observer
        ]
    elif not observer:
        return []
    else:
        return [
            SeeChallengesButton(secret, True) for secret in sorted(team.revealed_secrets)
            if not secret.claimed or secret.owner != observer
        ]


def mapRow(observer: Team | None = None) -> list[Button]:
    return [
        SearchStopButton(),
        CheckHandButton(observer, observer)
    ] if observer else []


def teamActionsRow(team: Team, victim: Team) -> list[Button]:
    if not team:
        return []
    codes = list(set([
        action.code for action in team.available_starting_actions
        if action.playableTeam(victim) and action.type != ActionType.CURSE
    ]))
    # TODO: this requires sorting!
    row = [
        PlayActionCodeButton(code, team, victim) for code in codes
    ]
    if team.available_curses:
        row.append(PlayCurseButton(victim))
    return row


def stopActionsRow(team: Team, stop: Stop) -> list[Button]:
    if not team:
        return []
    codes = list(set([
        action.code for action in team.available_starting_actions
        if action.type == ActionType.STEAL and action.playableSpecific(stop)
    ]))
    # TODO: this requires sorting!
    row = [
        PlayActionCodeButton(code, team, stop.owner, stop) for code in codes
    ]
  
    return row
    


def seeChallengesRow(stop: Stop) -> list[Button]:
    return [
        SeeChallengesButton(stop)
    ]


# generate action row (list of buttons potentially including NONE values)
# can result in none if no applicable buttons
# generate view
# can result in MISSING if no applicable action rows


def grid(*rows: list[Button] | None) -> View:
    rows = [row for row in rows if row]
    if not rows:
        return MISSING
    # now construct the view
    grid = View(timeout=None)
    # assign the rows and add them!
    for i, row in enumerate(rows):
        for button in row:
            button.row = i
            grid.add_item(button)
    # return completed grid
    return grid

# HEREEEEE COME THE BUTTON CLASSES :D


class MapButton(Button):
    '''SECONDARY'''

    def __init__(self):
        super().__init__(style=ButtonStyle.secondary,
                         label="Check map",
                         emoji="🗺️")

    async def callback(self, ctx: Interaction):
        # use standard command if possible
        if getObserver(ctx):
            from check import map
            await map(ctx)
            return
        await ctx.response.defer()
        # check if live
        live_game = game(ctx.guild)
        role_team = team(ctx.user.top_role)
        # send to their private channel if applicable (SHOULD JUST BE EPHERMAL REALLY)
        if role_team:
            channel = ctx.guild.get_channel(
                channel_id(role_team))
        else:
            channel = ctx.channel
        # send them a map!
        await sendMessage(channel, f"{mention(role_team)}" if role_team else None, embed_map(
            live_game, role_team), view=grid(mapRow(role_team)))


class CheckHandButton(Button):
    '''SUCCESS/SECONDARY'''

    def __init__(self, team: Team, observer: Team | None = None):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.success if team == observer else ButtonStyle.secondary,
                         label=f"{mentionPossessive(
                             team, observer, use_role=False)} hand",
                         emoji="🃏")
        # save some things
        self.target = team

    async def callback(self, ctx: Interaction):
        # use standard command if possible
        if getObserver(ctx):
            from check import hand
            await hand(ctx, self.target.name)
            return
        # check if live
        live_game = game(ctx.guild, True, True)
        # doesn't work if not live
        if not live_game:
            if not live_game:
                await complain(ctx, "Not in a game", "You can only check a team's hand during a game.")
                return
        # postpone
        await ctx.response.defer()
        role_team = team(ctx.user.top_role)
        # send to their private channel if applicable (SHOULD JUST BE EPHERMAL REALLY)
        if role_team:
            channel = ctx.guild.get_channel(
                channel_id(role_team))
        else:
            channel = ctx.channel
        # send them the cards! (also action cards if looking at own hand)
        if self.target == role_team:
            await sendMessage(channel, f"{mention(role_team)}" if role_team else None, embed_unlocked_stops(
                self.target, role_team), embed_locked_lines(self.target, role_team), embed_available_actions(self.target, role_team),
                view=grid(
                    checkHandRow(self.target, role_team),
                    claimableLinesRow(role_team)
            ))
        else:
            await sendMessage(channel, f"{mention(role_team)}" if role_team else None, embed_unlocked_stops(
                self.target, role_team), embed_locked_lines(self.target, role_team),
                view=grid(
                    checkHandRow(self.target, role_team),
                    teamActionsRow(role_team, self.target)
            ))


class CheckSecretsButton(Button):
    '''DANGER'''

    def __init__(self, team: Team, observer: Team | None = None):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.danger,
                         label=f"Check secrets" if team == observer else "Check revealed secrets",
                         emoji="✉️")
        self.target = team

    async def callback(self, ctx: Interaction):
        # use standard command if possible
        if getObserver(ctx):
            from check import secret_cards
            await secret_cards(ctx, self.target.name)
            return
        # check if live
        live_game = game(ctx.guild, True, True)
        # doesn't work if not live
        if not live_game:
            if not live_game:
                await complain(ctx, "Not in a game", "You can only check a team's secret cards during a game.")
                return
        # postpone
        await ctx.response.defer()
        role_team = team(ctx.user.top_role)
        # send to their private channel if applicable (SHOULD JUST BE EPHERMAL REALLY)
        if role_team:
            channel = ctx.guild.get_channel(
                channel_id(role_team))
        else:
            channel = ctx.channel
        # send them the cards! (also action cards if looking at own hand)
        if self.target == role_team:
            await sendMessage(channel, None, embed_secrets(self.target),
                              view=grid(
                checkSecretsRow(self.target, role_team),
                secretChallengesRow(self.target, role_team)

            ))
        else:
            await sendMessage(channel, None, embed_revealed_secrets(self.target, role_team),
                              view=grid(
                checkSecretsRow(self.target, role_team),
                secretChallengesRow(self.target, role_team)
            ))


class CheckCursesButton(Button):
    '''DANGER'''

    def __init__(self, team: Team, observer: Team | None = None):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.danger,
                         label=f"Check current curses",
                         emoji="☠️")
        self.target = team

    async def callback(self, ctx: Interaction):
        # use standard command if possible
        from check import active_curses
        await active_curses(ctx, self.target.name)



class CheckLineButton(Button):
    '''SECONDARY'''

    def __init__(self, line: Line):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.danger,
                         label=f"Check {line.colour} line",
                         emoji=line.emoji)
        self.line = line

    async def callback(self, ctx: Interaction):
        from check import line
        # use standard command if possible
        await line(ctx, self.line.colour)


class SearchStopButton(Button):
    '''SECONDARY'''

    def __init__(self, another: bool = False):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.secondary,
                         label=f"See another stop" if another else "Search for a stop",
                         emoji="📌")

    async def callback(self, ctx: Interaction):
        # ask for a stop
        channel_team = team(ctx.channel)

        def check(message: Message) -> bool:
            return (message.channel.id == channel_id(channel_team)
                    and message.author.top_role.id == role_id(channel_team))
        prompt = await sendMessage(ctx, "What is the name of the stop you'd like to check?")
        message: Message = await ctx.client.wait_for('message', check=check, timeout=120)
        # check if the message is sufficient
        if (not message) or (not message.content):
            await complain(message if message else ctx.channel, "No stop name provided.", "Please try again by using the button.")
            return
        stop = channel_team.game.searchStop(message.content)
        if not stop:
            # send complaint
            await complain(message, "Invalid stop name.", "Try again with a correct tram stop name by using the button.")
            await prompt.delete()
            return
        # create embed
        if not stop.claimed:
            await sendMessage(message, None, embed_stop(stop, channel_team), embed_challenges(stop),
                              view=grid(
                checkStopRow(stop, channel_team),
                stopActionsRow(channel_team, stop)
            ))
        else:
            await sendMessage(message, None, embed_stop(stop, channel_team),
                              view=grid(
                checkStopRow(stop, channel_team),
                stopActionsRow(channel_team, stop)
            ))


class CompleteChallengeButton(Button):
    '''SUCCESS'''

    def __init__(self, team: Team):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.success,
                         label=f"Completed")

    async def callback(self, ctx: Interaction):
        from challenge import complete
        await complete(ctx)


class VetoChallengeButton(Button):
    '''DANGER'''

    def __init__(self, team: Team):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.danger,
                         label=f"Veto ({int(team.current_challenge.veto_period.total_seconds() // 60)} minute penalty)")

    async def callback(self, ctx: Interaction):
        from challenge import veto
        await veto(ctx)


class ResumeChallengeButton(Button):
    '''PRIMARY'''

    def __init__(self, team: Team):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.primary,
                         label=f"Resume '{team.paused_challenge.title}'")

    async def callback(self, ctx: Interaction):
        from challenge import resume
        await resume(ctx)


class StartChallengeButton(Button):
    '''SECONDARY'''

    def __init__(self, challenge: Challenge, index: int, team: Team):
        # mention the team here (vary colour based on who's asking)
        emoji_code = getEmojiCode('challenge_'+str(index+1))
        emoji_name = emoji_code.split(':')[1]
        emoji_id = emoji_code.split(':')[2].removesuffix('>')
        # disable the button if it cannot be used
        super().__init__(style=ButtonStyle.secondary,
                         label=f"Start '{challenge.title}'",
                         emoji=PartialEmoji(name=emoji_name, id=emoji_id),
                         disabled=team.game.game_over or challenge.location.claimed or team.in_veto or team.in_challenge or not team.may_progress)
        self.challenge = challenge

    async def callback(self, ctx: Interaction):
        from challenge import start
        live_game = game(ctx.guild, True)
        # validate stuff!!
        if not live_game:
            await complain(ctx, "Not in a game", "You can only start challenges during a game.")
            return
        channel_team = team(ctx.channel)
        # make sure we're in the correct channel
        if channel_team.in_veto:
            await complain(ctx, "Currently in veto period", f"You cannot start challenges until your veto period ends {countdownTo(channel_team.veto_end)}.")
            return
        elif channel_team.in_challenge:
            await complain(ctx, "Currently completing another challenge", f"You cannot start another challenge until you complete or veto {channel_team.current_challenge.title} at {channel_team.current_challenge_location.name}.")
            return
        elif not channel_team.may_progress:
            await complain(ctx, "Cannot currently progress in game", f"You cannot start another challenge until you clear any clearable curses.")
            return
        # ok so get a photo...
        def check(message: Message) -> bool:
            return (message.channel.id == channel_id(channel_team)
                    and message.author.top_role.id == role_id(channel_team))
        prompt = await sendMessage(ctx, f"Upload a selfie on the {self.challenge.location.name} tram platform to start '{self.challenge.title}'...")
        message: Message = await ctx.client.wait_for('message', check=check, timeout=120)
        # check if the message is sufficient
        if (not message) or (not message.attachments):
            await complain(message if message else ctx.channel, "No image provided.", "You must provide a selfie to begin any challenge.")
            await prompt.delete()
            return
        # take the first one and start the challenge! :)
        await start(ctx,
                    self.challenge.location.code,
                    self.challenge.title,
                    message.attachments[0])


class PlayAnyActionButton(Button):
    '''PRIMARY'''

    def __init__(self, team: Team):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.primary,
                         label=f"Play an action card",
                         emoji="✨",
                         disabled=team.in_veto or not team.may_progress)

    async def callback(self, ctx: Interaction):
        from play import play_action_card
        await play_action_card(ctx)


class PlaySpecificActionButton(Button):
    '''PRIMARY'''

    def __init__(self, action: Action, victim: Team | None = None, target: Stop | None = None):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.primary,
                         label=f"Use {action.title} on this stop" if target else (
                             f"Use {action.title} on this team" if victim else
                             f"Play {action.title}"
                         ),
                         emoji=action.emoji,
                         disabled=action.owner.in_veto or not action.owner.may_progress)
        self.action = action
        self.victim = victim
        self.target = target

    async def callback(self, ctx: Interaction):
        from play import play_specific_action_card
        await ctx.response.defer()
        # do that!! (validation is contained)
        await play_specific_action_card(ctx, self.action, self.victim, self.target)


class PlayActionCodeButton(Button):
    '''SECONDARY'''

    def __init__(self, action_code: str, owner:Team, victim: Team | None = None, target: Stop | None = None):
        # mention the team here (vary colour based on who's asking)
        action = Action(action_code)
        super().__init__(style=ButtonStyle.secondary,
                         label=f"Use {action.title} on this stop" if target else (
                             f"Use {action.title} on this team" if victim else
                             f"Play {action.title}"
                         ),
                         emoji=Action(action_code).emoji,
                         disabled=owner.in_veto or not owner.may_progress)
        self.action_code = action_code
        self.victim = victim
        self.target = target

    async def callback(self, ctx: Interaction):
        from play import play_specific_action_card
        # determine what zone to play
        live_game = game(ctx.guild, True)
        # validate stuff!!
        if not live_game:
            await complain(ctx, "Not in a game", "You can only start challenges during a game.")
            return
        channel_team = team(ctx.channel)
        if not self.action_code in [action.code for action in channel_team.available_starting_actions]:
            await complain(ctx.channel, "Not your action card", "You don't have this action card in your hand.")
            return
        await ctx.response.defer()
        # check if there is a zone choice...
        zones = list(
            set([action.zone for action in channel_team.getActionsByCode(self.action_code)]))
        # oh no gotta choose one
        if len(zones) > 1:
            # gotta do some stuff...
            zone_choice = ActionZoneChoice(zones)
            message = await sendMessage(ctx, f"Choose which zone to play a {Action(self.action_code).title} card from...", embed_zone_options(channel_team, self.action_code), view=zone_choice)
            # wait for them to make a choice
            await zone_choice.wait()
            await message.edit(view=zone_choice)
            # make sure they actually chose one
            chosen_zone = zone_choice.chosen_zone
            if not chosen_zone:
                await complain(ctx.channel, "No zone chosen", f"You didn't choose a zone.")
                return
        else:
            chosen_zone = zones[0]
        # yayyyy
        action = channel_team.getActionByCodeAndZone(
            self.action_code, chosen_zone)
        # do that!! (validation is contained)
        await play_specific_action_card(ctx, action, self.victim, self.target)


class PlayCurseButton(Button):
    '''DANGER'''

    def __init__(self, victim: Team | None = None):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.danger,
                         label=f"Curse {
                             victim.name}" if victim else "Play a curses",
                         emoji="☠️")
        self.victim = victim

    async def callback(self, ctx: Interaction):
        from play import play_curse
        await ctx.response.defer()
        # USE CHOSEN VICTIM!
        await play_curse(ctx, self.victim.name)


class SeeChallengesButton(Button):
    '''SECONDARY'''

    def __init__(self, stop: Stop, name: bool = False):
        super().__init__(style=ButtonStyle.secondary,
                         label=f"{
                             stop.name} challenges" if name else "See challenges",
                         emoji="📋")
        self.stop = stop

    async def callback(self, ctx: Interaction):
        from preview import challenges
        # send them the challenges
        await challenges(ctx, self.stop.code)


class ClaimLineButton(Button):
    '''SUCCESS'''

    def __init__(self, line: Line):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.secondary,
                         label=f"Claim {line.colour} line",
                         emoji=line.emoji)
        self.line = line

    async def callback(self, ctx: Interaction):
        from more import claim_line
        await claim_line(ctx, self.line.colour)


class ClearCurseButton(Button):
    '''SECONDARY'''

    def __init__(self, curse: ClearCurse):
        # mention the team here (vary colour based on who's asking)
        super().__init__(style=ButtonStyle.secondary,
                         label=f"Clear '{curse.title}'",
                         emoji="✅")
        self.curse = curse

    async def callback(self, ctx: Interaction):
        from more import clear_curse
        await clear_curse(ctx, self.curse.title)
