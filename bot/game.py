from discord import Guild, Message
from discord.ui import View
from utils.data import game, channel_id, countdownTo, getUpdatesChannel, getEvidenceChannel, mention, deleteSelfies
from utils.responses import sendMessage
from utils.embeds import embed_secrets, embed_map, embed_unlocked_stops, embed_locked_lines
from utils.views import MulliganChoice
from asyncio import sleep
from utils.buttons import grid, mapRow, checkSecretsRow, secretChallengesRow
from datetime import datetime, timedelta


async def start_game(guild: Guild, countdown:int = 5, rewards:bool=True, secrets:bool=True):
    # deal secrets
    live_game = game(guild)
    # make sure game not started yet
    if live_game.in_progress:
        return
    #can be basic if needed
    if rewards:
        # show reward cards
        live_game.assignRewards()
    if secrets:
        # deal out initial secrets
        live_game.dealAllSecrets()
    # request mulligans
    views: list[View] = []
    messages: list[Message] = []
    start_time = datetime.now() + timedelta(minutes=countdown)
    for team in live_game.all_teams:
        channel = guild.get_channel(channel_id(team))
        # send request message
        views.append(MulliganChoice(team))
        await sendMessage(channel, f"The game will begin {countdownTo(start_time)}.",
                          embed_map(live_game, team),
                          view=grid(
                              mapRow(team)
                          ))
        messages.append(await sendMessage(channel, "Choose up to 3 stops to mulligan...",
                                          embed_secrets(team),
                                          view=views[-1]))
        await sendMessage(channel, view=grid(
            secretChallengesRow(team, team)
        ))
        await messages[-1].pin()
        
    # wait until the last one of them times out
    # wait 5 minutes :)
    await sleep(countdown*60)
    # edit all of them so that they're disabled 
    for i, message in enumerate(messages):
        views[i].disable_all_items()
        await message.edit(view=views[i])
        await message.unpin()
    # start game (including mulligan)
    live_game.start()
    # now send new secrets
    for team in live_game.all_teams:
        channel = guild.get_channel(channel_id(team))
        # send request message
        await sendMessage(channel, "The game has begun! Here are your final secret cards.",
                          embed_map(live_game, team), embed_secrets(team),
                          view=grid(
                              mapRow(team),
                              secretChallengesRow(team, team)
                          ))
    # and send to main channel with full map for starting postition reference
    await sendMessage(getUpdatesChannel(guild), "The game has begun! Good luck to all teams.", embed_map(live_game),
                      view=mapRow())

def reset_game(guild: Guild):
    # reset it...
    live_game = game(guild)
    live_game.reset() #yay!
    #delete the selfies
    deleteSelfies(live_game)

def get_game_code(guild:Guild):
    live_game = game(guild, allow_game_over=True)
    if live_game:
        return live_game.id
    else:
        return "????"


async def end_game(guild: Guild):
    # find game
    live_game = game(guild)
    # say complete
    winner = live_game.winner
    total_time = live_game.total_game_time
    announcement = await sendMessage(getUpdatesChannel(guild), f"# 🎉🎉🎉 {mention(winner)} just won the game!\nTotal game time: **{total_time.total_seconds()//3600}h{(total_time.total_seconds()//60)%60}**", embed_locked_lines(winner), embed_unlocked_stops(winner))
    await announcement.pin()
    # send congratulations to that team including secrets :)
    await sendMessage(guild.get_channel(channel_id(winner)), f"# 🎉🎉🎉 You just won the game!\nGo and brag to the other teams in <#{getUpdatesChannel(guild).id}>", embed_locked_lines(winner, winner), embed_secrets(winner))

async def test(guild: Guild):
    # find game
    live_game = game(guild, allow_game_over=True)
    # send a message to all channels
    await getUpdatesChannel(guild).send("[updates channel]")
    await getEvidenceChannel(guild).send("[evidence channel]")
    for team in live_game.all_teams:
        await guild.get_channel(channel_id(team)).send(f"[{mention(team)} / {team.name}]")