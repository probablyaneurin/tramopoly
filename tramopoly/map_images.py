from __future__ import annotations
from .data import LIBRARY, LIVE, STATIC, IMAGES, ICONS
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Resampling
from .card_images import IconType, WHITE, SLIGHT_GRAY
from .data import getColour, getMapData, getIconData, getTeamColour, loadIcon
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .stop import Stop
    from .team import Team
    from .game import Game, getAllStops

#these store DESIRED WIDTH AND HEIGHT
WIDTH = 2040
HEIGHT = int((2320/2040)*WIDTH)
CIRCLE_RADIUS = int(WIDTH/105)
BORDER_WIDTH = int(CIRCLE_RADIUS/7)
ICON_SIZE = int(1.2*CIRCLE_RADIUS)
DARKNESS_FACTOR = 0.8
MAP = Image.open(LIBRARY / STATIC / IMAGES / "map.png")

def drawMap(game: Game | None = None, observer: Team | None = None) -> Image.Image:
    from .game import getAllStops
    # load in base image
    map = MAP.copy()
    # resize to set height
    map = map.resize((WIDTH, HEIGHT))
    # load in map data
    map_data = getMapData()
    # save original width and height
    o_width, o_height = map_data["map_size"][0], map_data["map_size"][1]
    # now draw on every stop
    stops = game.all_stops if game else getAllStops()
    draw = ImageDraw.Draw(map, "RGBA")
    for stop in stops:
        # get coordinates
        addStop(draw, stop, (map_data["stop_placements"][stop.code][0],
                map_data["stop_placements"][stop.code][1]), (o_width, o_height), observer)
    # return completed image
    return map


def addStop(draw: ImageDraw.ImageDraw, stop: Stop, coordinates: tuple[int, int], o_size: tuple[int, int], observer: Team | None = None):
    secret = observer and stop in observer.secrets
    # determine icon
    icon_type = stop.map_icon(observer)
    # find center of main circle
    center = (WIDTH * float(coordinates[0]) / float(o_size[0]),
              HEIGHT * float(coordinates[1]) / float(o_size[1]))
    # secret must always be shown
    if secret and not icon_type == IconType.SECRET:
        # add outline instead if no icon used
        secret_data = getIconData(str(IconType.SECRET.value))
        draw.circle(center, int(1.3*CIRCLE_RADIUS),
                    getColour(secret_data["colour"]))
    # load in icon and default colour
    colour = WHITE
    if icon_type != IconType.NONE:
        icon_data = getIconData(str(icon_type.value))
        icon = loadIcon(icon_data["icon"][0]).resize((ICON_SIZE, ICON_SIZE))
        colour = getColour(icon_data["colour"])
    # use team colour if claimed in any way
    if icon_type in [IconType.CLAIMED_YOU, IconType.CLAIMED_OTHER, IconType.LOCKED_YOU, IconType.LOCKED_OTHER]:
        colour = getColour(getTeamColour(stop.owner.colour))
    # draw main circle
    draw.circle(center, CIRCLE_RADIUS, WHITE)
    # draw inner circle
    draw.circle(center, CIRCLE_RADIUS-BORDER_WIDTH, colour,
                darken(colour), BORDER_WIDTH)
    # choose icon and COLOUR ICON to the required team colour
    if icon_type != IconType.NONE:
        icon_white = Image.new("RGB", (ICON_SIZE, ICON_SIZE), WHITE)
        draw._image.paste(icon_white, (
            int(center[0] - 0.5*ICON_SIZE),
            int(center[1] - 0.5*ICON_SIZE)
        ), icon)


def darken(colour: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple([int(amount * DARKNESS_FACTOR) for amount in colour])
