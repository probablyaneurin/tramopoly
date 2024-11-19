from pathlib import Path
from PIL import Image
from json import load, dump
from typing import Any

LIBRARY = Path(__file__).parent

LIVE = "live"
STATIC = "static"
DATA = "data"
IMAGES = "images"
ICONS = "icons"
FONTS = "fonts"

### STATIC ###


def getStaticLineData(colour: str) -> dict[str, Any]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "lines.json") as source:
        lines = load(source)
    # find correct stop
    return lines[colour]


def getStaticStopData(code: str) -> dict[str, Any]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "stops.json") as source:
        stops = load(source)
    # find correct stop
    return stops[code]


def getStaticActionData(code: str) -> dict[str, Any]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "actions.json") as source:
        actions = load(source)
    # find correct stop
    return actions[code]


def getAllStopCodes() -> list[str]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "stops.json") as source:
        stops = load(source)
    # return all stop codes
    return list(stops.keys())


def getAllLineColours() -> list[str]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "lines.json") as source:
        lines = load(source)
    # return all line colours
    return list(lines.keys())


def getStaticLineData(colour: str) -> dict[str, Any]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "lines.json") as source:
        lines = load(source)
    # find correct stop
    return lines[colour]


def getStaticSpecialAbilityData(code: str) -> dict[str, Any]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "special_abilities.json") as source:
        abilities = load(source)
    # find correct ability
    return abilities[code]


def getAllSpecialAbilityCodes() -> list[str]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "special_abilities.json") as source:
        abilities = load(source)
    # return just the codes
    return list(abilities.keys())


def getAllZoneNumbers() -> list[int]:
    # generate zones from 1 to 4
    return [number for number in range(1, 5)]


def getSearchDict() -> dict[str, str]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "search.json") as source:
        search_dict = load(source)
    # return entire dictionary
    return search_dict


def getChallengeData(id: str) -> dict[str, Any]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "challenges.json") as source:
        challenges = load(source)
    # find correct stop
    return challenges[id]


def getIconData(type: str) -> dict[str, Any]:
    if hasattr(type, 'value'):
        type = str(type.value)
    # open static file
    with open(LIBRARY / STATIC / DATA / "icons.json") as source:
        icons = load(source)
    # choose correct chip
    return icons[type]


def getActionTypeData(type: str) -> dict[str, Any]:
    if hasattr(type, 'value'):
        type = str(type.value)
    # open static file
    with open(LIBRARY / STATIC / DATA / "action_types.json") as source:
        types = load(source)
    # choose correct action type
    return types[type]


def getMapData() -> dict[str, Any]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "map.json") as source:
        map = load(source)
    # return entire dictionary
    return map


def getStartDeckData(zone_number: int) -> list[str]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "start_decks.json") as source:
        decks = load(source)
    # return just this zone's starting deck
    return decks[str(zone_number)]


def getRewardPlacementData() -> list[dict[str, Any]]:
    # open static file
    with open(LIBRARY / STATIC / DATA / "rewards.json") as source:
        placements = load(source)
    # return entire list of placements
    return placements

### LIVE ###


def getLiveStopData(code: str, game_id: str) -> dict[str, Any]:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "stops.json") as source:
        stops = load(source)
    # find correct stop
    if code in stops:
        return stops[code]
    # or use default
    else:
        return {}


def setLiveStopData(code: str, data: dict[str, Any], game_id: str) -> None:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "stops.json") as source:
        stops = load(source)
    # set this stop's new data
    stops[code] = data
    # save live file
    with open(LIBRARY / LIVE / game_id / DATA / "stops.json", 'w') as source:
        dump(stops, source, indent=4)


def getAllTeamIDs(game_id: str) -> list[str]:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "teams.json") as source:
        teams = load(source)
    # return all team IDs
    return list(teams.keys())


def getLiveTeamData(id: str, game_id: str) -> dict[str, Any]:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "teams.json") as source:
        teams = load(source)
    # find correct stop
    if id in teams:
        return teams[id]
    # or use default
    else:
        return {}


def setLiveTeamData(id: str, data: dict[str, Any], game_id: str) -> None:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "teams.json") as source:
        teams = load(source)
    # set this team's new data
    teams[id] = data
    # save live file
    with open(LIBRARY / LIVE / game_id / DATA / "teams.json", 'w') as source:
        dump(teams, source, indent=4)


def getLivePendingCounter(action_id: str, game_id: str) -> dict[str, Any]:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "counters.json") as source:
        counters = load(source)
    # find correct card
    if action_id in counters:
        return counters[action_id]
    else:
        return {}


def setLivePendingCounter(action_id: str, data: dict[str, Any], game_id: str) -> None:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "counters.json") as source:
        counters = load(source)
    # add new data
    counters[action_id] = data
    # save live file
    with open(LIBRARY / LIVE / game_id / DATA / "counters.json", 'w') as source:
        dump(counters, source, indent=4)


def getLiveDeckData(game_id: str) -> dict[str, Any]:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "deck.json") as source:
        deck = load(source)
    # return entire dictionary
    return deck


def setLiveDeckData(data: dict[str, Any], game_id: str) -> None:
    # open live file and save new data
    with open(LIBRARY / LIVE / game_id / DATA / "deck.json", 'w') as source:
        dump(data, source, indent=4)


def getLiveActionData(id: str, game_id: str) -> dict[str, Any]:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "deck.json") as source:
        deck = load(source)
    # find correct action
    return deck[id]


def setLiveActionData(id: str, data: dict[str, Any], game_id: str) -> None:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "deck.json") as source:
        deck = load(source)
    # set this action's new data
    deck[id] = data
    # save live file
    with open(LIBRARY / LIVE / game_id / DATA / "deck.json", 'w') as source:
        dump(deck, source, indent=4)


def getLiveGameData(game_id: int) -> dict[str, Any]:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "game.json") as source:
        data = load(source)
    # return entire dictionary
    return data

def setLiveGameData(game_id: int, data: dict[str, Any]) -> None:
    # open live file
    with open(LIBRARY / LIVE / game_id / DATA / "game.json", 'w') as source:
        dump(data, source)

def resetLiveGameData(game_id: int) -> None:
    (LIBRARY / LIVE / game_id / DATA / "stops.json").write_text("{}")
    (LIBRARY / LIVE / game_id / DATA / "deck.json").write_text("{}")
    (LIBRARY / LIVE / game_id / DATA / "counters.json").write_text("{}")
    (LIBRARY / LIVE / game_id / DATA / "game.json").write_text('{"in_progress": false}')
    # teams are reset separately


def getAllGameIDs() -> list[str]:
    # use names of directories in live folder
    return [path.stem for path in (LIBRARY / LIVE).iterdir()]


def createNewGameDirectory(id: str) -> bool:
    try:
        (LIBRARY / LIVE / id / DATA).mkdir(parents=True)
        (LIBRARY / LIVE / id / DATA / "stops.json").write_text("{}")
        (LIBRARY / LIVE / id / DATA / "teams.json").write_text("{}")
        (LIBRARY / LIVE / id / DATA / "deck.json").write_text("{}")
        (LIBRARY / LIVE / id / DATA / "counters.json").write_text("{}")
        (LIBRARY / LIVE / id / DATA / "game.json").write_text('{"in_progress": false}')
        return True
    except:
        return False


def getColour(colour: str) -> tuple[int, int, int]:
    # return as tuple from hex
    return (int(colour[0:2], 16), int(colour[2:4], 16), int(colour[4:6], 16))


def getTeamColour(colour: str) -> str:
    # open static file
    with open(LIBRARY / STATIC / DATA / "team_colours.json") as source:
        colours = load(source)
    # return all line colours
    return colours[colour]


def loadIcon(code: str) -> Image.Image:
    return Image.open(LIBRARY / STATIC / IMAGES / ICONS / (code + ".png"))


def clean(search_term: str) -> str:
    search_term_clean = ""
    for c in search_term:
        if c.isalnum():
            search_term_clean += c.lower()
        elif c == '-' or c == ' ':
            search_term_clean += ' '
    return search_term_clean
