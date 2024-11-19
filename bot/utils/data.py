from discord import Guild, TextChannel, Role, Interaction, Attachment, File
from tramopoly import Game, Team, Challenge
from typing import Any
from json import load
from pathlib import Path
from datetime import datetime


def game(guild: Guild, in_progress:bool=False, allow_game_over:bool=False) -> Game | None:
    # load file of current game
    guild_data = getGuildData(guild)
    # check if the current guild is actually running a game
    if not guild_data:
        return None
    # now create the game
    live_game = Game(guild_data["game"])
    if not allow_game_over and in_progress and not live_game.in_progress:
        return None
    elif allow_game_over and live_game.game_over:
        return live_game
    else:
        return live_game


def team(channel_or_role: TextChannel | Role) -> Team | None:
    # now get the data in this guild
    guild_data = getGuildData(channel_or_role.guild)
    # make sure it's actually a current game
    if not guild_data:
        return None
    id = str(channel_or_role.id)
    # now determine the type of argument
    if isinstance(channel_or_role, TextChannel) and id in guild_data["channels"]:
        # get it from the channel
        return Team(guild_data["channels"][id], Game(guild_data["game"]))
    elif isinstance(channel_or_role, Role) and id in guild_data["roles"]:
        # get it from the role
        return Team(guild_data["roles"][id], Game(guild_data["game"]))
    # no matching channel or role
    return None


def role_id(team: Team) -> int:
    # get guild data
    guild_data = getGuildData(guild_id(team.game))
    # find a matching role
    return next(int(id) for id in guild_data["roles"] if guild_data["roles"][id] == team.id)


def channel_id(team: Team) -> int:
    # get guild data
    guild_data = getGuildData(guild_id(team.game))
    # find a matching role
    return next(int(id) for id in guild_data["channels"] if guild_data["channels"][id] == team.id)


def guild_id(game: Game) -> Guild:
    # load file
    with open(LIBRARY / LIVE / "guilds.json") as source:
        data = load(source)
    # find a matching guild
    return next(int(id) for id in data if data[id]["game"] == game.id)


LIBRARY = Path(__file__).parent.parent
LIVE = "live"
STATIC = "static"


def token() -> str:
    with open(LIBRARY / STATIC / "token.txt") as file:
        token = file.readline()
    return token


def getGuildData(guild: Guild | int) -> dict[str, dict[str, Any]]:
    # load file
    guild_id = str(guild.id if isinstance(guild, Guild) else guild)
    with open(LIBRARY / LIVE / "guilds.json") as source:
        data = load(source)
    # use default value if needed
    if guild_id in data:
        return data[guild_id]
    else:
        return {}


def getUpdatesChannel(guild: Guild) -> TextChannel:
    return guild.get_channel(int(getGuildData(guild)["updates"]))

def getEvidenceChannel(guild: Guild) -> TextChannel:
    return guild.get_channel(int(getGuildData(guild)["evidence"]))



def getEmojiCode(name: str) -> str:
    # load file
    with open(LIBRARY / STATIC / "emoji.json") as source:
        data = load(source)
    # use default value if needed
    return data[name]


def getObserver(ctx: Interaction) -> Team | None:
    channel_team = team(ctx.channel)
    role_team = team(ctx.user.top_role)
    if channel_team and channel_team == role_team:
        return channel_team
    return None


def mention(team: Team, observer: Team | None = None, capitalise: bool = True, use_role: bool = True) -> str:
    if team == observer:
        return "You" if capitalise else "you"
    else:
        return f"<@&{role_id(team)}>" if use_role else team.name


def mentionPossessive(team: Team, observer: Team | None = None, capitalise: bool = True, use_role: bool = True) -> str:
    if team == observer:
        return "Your" if capitalise else "your"
    else:
        return f"<@&{role_id(team)}>'s" if use_role else team.name + "'s"


def mentionChat(team: Team) -> str:
    # get team channel
    return f"<#{channel_id(team)}>"

def countdownTo(timestamp: datetime) -> str:
    return f"<t:{str(int(timestamp.timestamp()))}:R>"

def exactTime(timestamp: datetime) -> str:
    return f"<t:{str(int(timestamp.timestamp()))}:T>"

async def submitSelfie(team: Team, challenge: Challenge, selfie: Attachment):
    suffix = Path(selfie.filename).suffix
    #make sure it exists!
    (LIBRARY / LIVE / team.game.id).mkdir(exist_ok=True)
    # maintain image extension
    path = LIBRARY / LIVE / team.game.id/ f"{challenge.id}-{team.id}{suffix}"
    # save selfie
    await selfie.save(path)

def deleteSelfies(game: Game):
    #make sure it exists!
    if not (LIBRARY / LIVE / game.id).exists():
        return
    for file in (LIBRARY / LIVE / game.id).iterdir():
        file.unlink()
    (LIBRARY / LIVE / game.id).rmdir()
    # maintain image extension

def getSelfie(team: Team, challenge: Challenge) -> File:
    filename = getSelfieFilename(team, challenge)
    return File(LIBRARY / LIVE / team.game.id / filename, filename)

def getSelfieFilename(team: Team, challenge: Challenge) -> str:
    path = LIBRARY / LIVE / team.game.id
    return next(p for p in path.iterdir() if p.name.split('.')[0] == f"{challenge.id}-{team.id}").name