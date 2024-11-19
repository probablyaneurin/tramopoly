from __future__ import annotations
from .data import LIBRARY, STATIC, FONTS, IMAGES
from pathlib import Path  # for map
from PIL import Image, ImageDraw, ImageFont
from math import ceil, sin, degrees
import random
from enum import Enum
from .data import getIconData, getColour, loadIcon, getActionTypeData, getTeamColour
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .stop import Stop
    from .team import Team
    from .action import Action
    from .card import Card
    from .special import Special
    from .line import Line


def getCornerMask() -> Image.Image:
    mask = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, WIDTH, HEIGHT), SPACE*5, (0, 0, 0))
    return mask


def getSpecialGraphic() -> Image.Image:
    size = (int(WIDTH*0.5625), int(WIDTH*0.7625))
    graphic = Image.open(LIBRARY / STATIC / IMAGES /
                         "special_graphic.png").resize(size)
    return graphic


WIDTH = 800
HEIGHT = int(1.4 * WIDTH)
SPACE = int(0.04 * WIDTH)
HALF_SPACE = int(0.5 * SPACE)
BORDER_WIDTH = int(0.02 * WIDTH)
CORNER_MASK = getCornerMask()
SPECIAL_GRAPHIC = getSpecialGraphic()

HEADER_HEIGHT = SPACE*10
CHIP_HEIGHT = SPACE*3
ICON_SIZE = int(0.8*CHIP_HEIGHT)
CHIP_SPACE = int((CHIP_HEIGHT-ICON_SIZE)/2)


SHADED_HEIGHT = int(0.65*HEIGHT)
HEXAGON_RADIUS = int(0.4*SHADED_HEIGHT)
HEXAGON_CENTER = int(0.5*(SPACE*4.5 + SHADED_HEIGHT))
ACTION_ICON_SIZE = int(0.7*HEXAGON_RADIUS)

SHADING = (224, 224, 224)
BORDER = (204, 204, 204)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BACKGROUND = WHITE
SLIGHT_GRAY = (245, 245, 245)


WHITE_ICON = Image.new("RGB", (ICON_SIZE, ICON_SIZE), WHITE)
BLACK_ICON = Image.new("RGB", (ICON_SIZE, ICON_SIZE), BLACK)

TITLE_FONT = ImageFont.truetype(
    LIBRARY / STATIC / FONTS / "bold.ttf", int(0.26*HEADER_HEIGHT)
)

FOOTER_FONT = ImageFont.truetype(
    LIBRARY / STATIC / FONTS / "bold.ttf", int(0.6*CHIP_HEIGHT))

MAX_ROW = 4
MAX_ROTATION = 0.08
COLLECTION_SPACING = int(WIDTH*sin(MAX_ROTATION))
VISIBLE_HEIGHT = SPACE*2 + HEADER_HEIGHT


class IconType(Enum):
    NONE = -1
    CHALLENGE = 0
    REWARD = 1
    SPECIAL_ABILITY = 2
    CLAIMED_YOU = 3
    CLAIMED_OTHER = 4
    LOCKED_YOU = 5
    LOCKED_OTHER = 6
    TRAPPED = 7
    SECRET = 8
    VETO = 9


class CollectionStyle(Enum):
    HORIZONTAL = 1
    STACKED = 2


def drawStop(stop: Stop, observer: Team | None = None) -> Image.Image:
    # ok draw things
    card = getCardBase()
    # create draw
    draw = ImageDraw.Draw(card)
    # add shading
    draw.circle((int(0.5*WIDTH), HEIGHT+SPACE*10),  SPACE*20, SHADING)
    # add outline
    drawOutline(draw, getColour(getIconData(IconType.SECRET)["colour"])
                if observer and stop in observer.secrets else BORDER)
    # remove center bit for zone
    zone_text = "ZONE " + stop.zone_string
    addFooter(draw, zone_text, SHADING)
    # add colours to top
    lines = stop.lines
    # calculate section width
    colour_width = int((WIDTH - SPACE * 4) /
                       (len(lines) if len(lines) > 1 else 2))
    # draw left colour
    draw.rounded_rectangle((SPACE*2, SPACE*2, int(0.5*WIDTH), SPACE*2+HEADER_HEIGHT),
                           SPACE*3, lines[0].rgb_colour, corners=(True, False, False, True))
    # draw right colour
    draw.rounded_rectangle((int(0.5*WIDTH), SPACE*2, WIDTH-SPACE*2, SPACE*2+HEADER_HEIGHT),
                           SPACE*3, lines[-1].rgb_colour, corners=(False, True, True, False))
    # draw middle colours
    index = 1
    for line in lines[1:-1]:
        draw.rectangle(getColourBounds(index, colour_width), line.rgb_colour)
        index += 1
    # add stop name
    wrapped_name = wrapText(stop.name, WIDTH - SPACE*6, TITLE_FONT, draw)
    # indicate multis
    title_colour = WHITE
    if stop.on_zone_border:
        # calculate bounding box
        box = draw.multiline_textbbox((int(0.5*WIDTH), int(SPACE*2.4) + int(0.5*HEADER_HEIGHT)),
                                      wrapped_name, TITLE_FONT, "mm", SPACE, "center")
        # draw rounded rectange
        draw.rounded_rectangle((box[0]-HALF_SPACE, box[1]-HALF_SPACE, box[2]+HALF_SPACE, box[3]+HALF_SPACE),
                               SPACE, WHITE, BLACK, int(0.3*BORDER_WIDTH))
        title_colour = BLACK
    # now draw the actual stop name
    draw.multiline_text((int(0.5*WIDTH), int(SPACE*2.4) + int(0.5*HEADER_HEIGHT)), wrapped_name,
                        title_colour, TITLE_FONT, "mm", SPACE, "center")
    # initialise chip index then draw all info chips
    index = 0
    # draw on challenge chips
    challenges = stop.challenges
    for challenge_index in range(0, 2):
        # just add challenge title
        index = addChip(draw, index, IconType.CHALLENGE,
                        challenges[challenge_index].title, challenge_index)
    # check for special ability
    if stop._game and stop.special:
        index = addChip(draw, index, IconType.SPECIAL_ABILITY,
                        stop.special.name)

    # only do the next bit if the stop is linked to a game
    if stop._game:
        # check if claimed
        if stop.claimed:
            if stop.owner == observer:
                # you own this stop
                index = addChip(draw, index, IconType.CLAIMED_YOU,
                                "You own this stop", colour=getColour(getTeamColour(stop.owner.colour)))
                # you've locked it into a line
                if stop.locked:
                    index = addChip(draw, index, IconType.LOCKED_YOU,
                                    f"Locked into {stop.locked_line.colour} line", colour=stop.locked_line.rgb_colour)
            else:
                # another team owns this stop
                index = addChip(draw, index, IconType.CLAIMED_OTHER,
                                f"Claimed by {stop.owner.name}...", colour=getColour(getTeamColour(stop.owner.colour)))
                # another team's locked it into a line
                if stop.locked:
                    index = addChip(draw, index, IconType.LOCKED_OTHER,
                                    f"Locked into {stop.locked_line.colour} line", colour=stop.locked_line.rgb_colour)
        else:
            # reward card available!
            if stop.has_reward:
                index = addChip(draw, index, IconType.REWARD,
                                "Action card available!")
        # check if secret
        if observer and stop in observer.secrets:
            index = addChip(draw, index, IconType.SECRET,
                            "Your secret card!")
    # remove corners
    card = removeCorners(card)
    # return image
    return card


def drawAction(action: Action) -> Image.Image:
    # ok draw things
    card = getCardBase()
    # create draw
    draw = ImageDraw.Draw(card)
    # add colour section
    type_data = getActionTypeData(action.type.value)
    draw.rectangle((0, 0, WIDTH, SHADED_HEIGHT),
                   getColour(type_data["colour"]))
    # add outline
    drawOutline(draw)
    # check if live otherwise give all zones available
    if action._game:
        zone_text = "ZONE " + str(action.zone.number)
    elif action._force_zone:
        zone_text = "ZONE " + str(action._force_zone)
    else:
        # all possible zones you could get this card from
        zone_text = "ZONE " + '/'.join([str(zone.number)
                                       for zone in action.possible_zones])
    addFooter(draw, zone_text, WHITE)
    # add tagline
    addTagline(draw, action.tagline)
    # draw a hexagon
    draw.regular_polygon((int(0.5*WIDTH), HEXAGON_CENTER, HEXAGON_RADIUS), 6,
                         fill=WHITE, outline=SLIGHT_GRAY, width=SPACE*2)
    # work out total height of all the stuff (1 space between icon and thingy)
    wrapped_title = wrapText(action.title.upper(),
                             WIDTH - SPACE*4, TITLE_FONT, draw)
    # get bounding box
    height = draw.multiline_textbbox(
        (0, 0), wrapped_title, TITLE_FONT, spacing=HALF_SPACE)[3]
    total_height = height + ACTION_ICON_SIZE + SPACE
    # now put it all together
    icon = action.icon.resize((ACTION_ICON_SIZE, ACTION_ICON_SIZE))
    card.paste(icon, (int(0.5*WIDTH - 0.5*ACTION_ICON_SIZE),
               int(HEXAGON_CENTER - 0.5*total_height)), icon)
    draw.multiline_text((int(0.5*WIDTH), int(HEXAGON_CENTER - 0.5*total_height + ACTION_ICON_SIZE + HALF_SPACE)),
                        wrapped_title, BLACK, TITLE_FONT, "ma", HALF_SPACE, "center")
    # add the rules
    rules = action.rules
    if action.code.startswith("CURSE-CLEAR"):
        rules = rules + " The victims of this curse may not complete challenges or play non-counter cards until they clear this curse."
    elif action.code.startswith("CURSE-ONGOING"):
        rules = rules + " The victims of this curse may continue in the game whilst its effects are ongoing."
    # make sure the font size is ok!
    size = 0.5*CHIP_HEIGHT
    font = ImageFont.FreeTypeFont(
        LIBRARY / STATIC / FONTS / "regular.ttf", size)
    wrapped_rules = wrapText(rules, WIDTH - SPACE*5, font, draw)
    height = draw.multiline_textbbox(
        (0, 0), wrapped_rules, font, spacing=HALF_SPACE)[3]
    while SPACE + SHADED_HEIGHT + height > HEIGHT - SPACE*3:
        size -= 1
        font = ImageFont.FreeTypeFont(
            LIBRARY / STATIC / FONTS / "regular.ttf", size)
        wrapped_rules = wrapText(rules, WIDTH - SPACE*5, font, draw)
        height = draw.multiline_textbbox(
            (0, 0), wrapped_rules, font, spacing=HALF_SPACE)[3]
    draw.multiline_text((SPACE*2 + HALF_SPACE, SHADED_HEIGHT + SPACE),
                        wrapped_rules, BLACK, font, "la", HALF_SPACE)
    # remove corners
    card = removeCorners(card)
    # return image
    return card


def drawSpecialAbility(special: Special) -> Image.Image:
    # ok draw things
    card = getCardBase(getColour(getIconData(IconType.SPECIAL_ABILITY)["colour"]))
    # create draw
    draw = ImageDraw.Draw(card)
    # add graphic
    card.paste(SPECIAL_GRAPHIC,
               (int(0.5*WIDTH - 0.5*SPECIAL_GRAPHIC.width), SPACE*5), SPECIAL_GRAPHIC)
    # add outline
    drawOutline(draw)
    # check if live otherwise give all zones available
    # add tagline
    addTagline(draw, "Special Ability")
    # work out total height of all the stuff (1 space between icon and thingy)
    wrapped_name = wrapText(special.name.upper(),
                            WIDTH - SPACE*6, TITLE_FONT, draw)
    # get bounding box
    height = draw.multiline_textbbox(
        (0, 0), wrapped_name, TITLE_FONT, spacing=HALF_SPACE)[3]
    total_height = height + ACTION_ICON_SIZE + SPACE + HALF_SPACE
    # now put it all together
    icon = loadIcon(special.icon_name).resize(
        (ACTION_ICON_SIZE, ACTION_ICON_SIZE))
    card.paste(icon, (int(0.5*WIDTH - 0.5*ACTION_ICON_SIZE),
                      int(SPACE*5 + 0.5*SPECIAL_GRAPHIC.height - 0.5*total_height)), icon)
    draw.multiline_text((int(0.5*WIDTH), int(SPACE*5 + 0.5*SPECIAL_GRAPHIC.height - 0.5*total_height + ACTION_ICON_SIZE + SPACE + HALF_SPACE)),
                        wrapped_name, BLACK, TITLE_FONT, "ma", HALF_SPACE, "center")
    # add the description
    description = special.description
    # make sure the font size is ok!
    size = 0.5*CHIP_HEIGHT
    font = ImageFont.FreeTypeFont(
        LIBRARY / STATIC / FONTS / "regular.ttf", size)
    wrapped_description = wrapText(description, WIDTH - SPACE*5, font, draw)
    height = draw.multiline_textbbox(
        (0, 0), wrapped_description, font, spacing=HALF_SPACE)[3]
    while SPACE*6 + SPECIAL_GRAPHIC.height + height > HEIGHT - SPACE*3:
        size -= 1
        font = ImageFont.FreeTypeFont(
            LIBRARY / STATIC / FONTS / "regular.ttf", size)
        wrapped_description = wrapText(
            description, WIDTH - SPACE*5, font, draw)
        height = draw.multiline_textbbox(
            (0, 0), wrapped_description, font, spacing=HALF_SPACE)[3]
    draw.multiline_text((int(0.5*WIDTH), SPACE*6 + SPECIAL_GRAPHIC.height),
                        wrapped_description, BLACK, font, "ma", HALF_SPACE)
    # remove corners
    card = removeCorners(card)
    # return image
    return card

# maximum number of chips is 5


def addChip(draw: ImageDraw.ImageDraw, index: int,  type: IconType, content: str, challenge_index: int = 0, colour:tuple[int, int, int]=None) -> int:
    # use chip type to determine colour and icon (MAP ICON WILL BE POPPED OUT IN DISCORD)
    data = getIconData(str(type.value))
    # use default colour if no override
    if not colour:
        colour = getColour(data["colour"])
    average_value = (colour[0] + colour[1] + colour[2])/3
    use_white = average_value < 128
    # get coords
    top = SPACE*3 + HEADER_HEIGHT + (CHIP_HEIGHT + SPACE)*index
    left = SPACE*2
    bottom = SPACE*3 + HEADER_HEIGHT + \
        (CHIP_HEIGHT + SPACE)*index + CHIP_HEIGHT
    right = WIDTH - SPACE*2
    # draw background rectangle
    draw.rounded_rectangle((left, top, right, bottom),
                           int(0.5*CHIP_HEIGHT), colour)
    # add icon
    icon = loadIcon(data["icon"][challenge_index]
                    ).resize((ICON_SIZE, ICON_SIZE))
    # draw on icon
    draw._image.paste(WHITE_ICON if use_white else BLACK_ICON, (left + CHIP_SPACE*2, top+CHIP_SPACE), icon)
    # create font
    size = int(0.5*CHIP_HEIGHT)
    font = ImageFont.FreeTypeFont(
        LIBRARY / STATIC / FONTS / "regular.ttf", size)
    # make sure font is correct size
    while draw.textlength(content, font) > WIDTH - SPACE*4 - ICON_SIZE - CHIP_SPACE*6:
        size -= 1
        font = ImageFont.FreeTypeFont(
            LIBRARY / STATIC / FONTS / "regular.ttf", size)
    # add content text
    draw.text((left+ICON_SIZE+CHIP_SPACE*4, top + int(0.6*CHIP_HEIGHT)),
              content, WHITE if use_white else BLACK, font, "lm")
    # then
    return index + 1


def getColourBounds(index: int, width: int):
    return ((SPACE*2+width*index, SPACE*2, SPACE*2+width*(index+1), SPACE*2+HEADER_HEIGHT))


def getCardBase(background: tuple[int, int, int] = BACKGROUND) -> Image.Image:
    return Image.new("RGBA", (WIDTH, HEIGHT), background)


def removeCorners(card: Image.Image) -> Image.Image:
    new_card = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    new_card.paste(card, mask=CORNER_MASK)
    return new_card


def wrapText(text: str, width: int, font: ImageFont.ImageFont, draw: ImageDraw.ImageDraw) -> str:
    # try adding words
    words = text.strip().replace('-', ' ').split()
    index = 0
    lines = [""]
    while index < len(words):
        save = lines[-1]
        if len(save) > 0:
            lines[-1] += " "
        lines[-1] += words[index]
        # don't add it if it's too long
        if draw.textlength(text=lines[-1], font=font) > width:
            if (len(save) == 0):  # wrap characters if the word itself is too long
                del lines[-1]
                wrapped = wrapCharacters(words[index], width, font, draw)
                lines.extend(wrapped)
                index += 1  # successfully added word
            else:
                lines[-1] = save
                lines.append("")  # start new line instead
        else:
            index += 1  # successfully added word
    return '\n'.join(lines)


def wrapCharacters(word: str, width: int, font: ImageFont.ImageFont, draw: ImageDraw.ImageDraw) -> list[str]:
    # try adding characters
    index = 0
    lines = [""]
    while index < len(word):
        save = lines[-1]
        lines[-1] += word[index]
        # don't add it if it's too long
        if draw.textlength(text=lines[-1], font=font) > width:
            lines[-1] = save
            lines.append(word[index])
        index += 1
    # all lines have been added!
    return lines


def drawOutline(draw: ImageDraw.ImageDraw, colour: tuple[int, int, int] = BORDER) -> None:
    draw.rounded_rectangle((SPACE, SPACE, WIDTH-SPACE, HEIGHT-SPACE),
                           radius=SPACE*4, width=BORDER_WIDTH, outline=colour)


def addFooter(draw: ImageDraw.ImageDraw, text: str, background: tuple[int, int, int]) -> None:
    width = draw.textlength(text, FOOTER_FONT)
    draw.rectangle((int(0.5*WIDTH - 0.5*width) - SPACE, HEIGHT-SPACE*2,
                   int(0.5*WIDTH + 0.5*width) + SPACE, HEIGHT), background)
    # add zone number
    draw.text((int(0.5*WIDTH), HEIGHT-SPACE),
              text, BLACK, FOOTER_FONT, "ms")


def addTagline(draw: ImageDraw.ImageDraw, text: str):
    draw.text((int(0.5*WIDTH), SPACE*3),
              text.upper(), BLACK, FOOTER_FONT, "mt")

# make card collections...


def drawCollection(cards: list[Card], style: CollectionStyle, observer: Team | None = None) -> Image.Image:
    if len(cards) == 1:
        return cards[0].image(observer)
    # set up image size
    if style == CollectionStyle.HORIZONTAL:
        rows = ceil(len(cards) / float(MAX_ROW))
        columns = len(cards) if rows == 1 else MAX_ROW
        collection = Image.new("RGBA", (columns*WIDTH + 2*COLLECTION_SPACING,
                                        rows*HEIGHT + 2*COLLECTION_SPACING), (0, 0, 0, 0))
    elif style == CollectionStyle.STACKED:
        collection = Image.new("RGBA", (WIDTH + 2*COLLECTION_SPACING,
                                        HEIGHT + VISIBLE_HEIGHT*(len(cards)-1) + 2*COLLECTION_SPACING), (0, 0, 0, 0))
    # add each card on one by one
    for i, card in enumerate(cards):
        # get its image (randomly rotated)
        angle = random.uniform(0, MAX_ROTATION)
        if i % 2 == 0:
            angle = -angle
        card_image = card.image(observer).rotate(
            degrees(angle), expand=True)
        # paste it onto the image
        if style == CollectionStyle.HORIZONTAL:
            coordinates = (COLLECTION_SPACING + (i % MAX_ROW) * WIDTH + int(0.5*WIDTH),
                           COLLECTION_SPACING + (i//MAX_ROW)*HEIGHT + int(0.5*HEIGHT))
        elif style == CollectionStyle.STACKED:
            coordinates = (COLLECTION_SPACING + int(0.5*WIDTH),
                           COLLECTION_SPACING + i*VISIBLE_HEIGHT + int(0.5*HEIGHT))
        # paste relative to the center
        collection.paste(card_image, (coordinates[0] - int(
            0.5*card_image.width), coordinates[1] - int(0.5*card_image.height)), card_image)
    # return complete image
    return collection


def drawLineCollection(lines: list[Line], observer: Team | None = None) -> Image.Image:
    # just draw a single line if required
    if len(lines) == 1:
        return drawCollection(sorted(lines[0].locked_stops), CollectionStyle.STACKED, observer)
    # create big image
    collection = Image.new("RGBA", (len(lines)*(WIDTH+COLLECTION_SPACING) + COLLECTION_SPACING, HEIGHT + VISIBLE_HEIGHT*2 + 2*COLLECTION_SPACING), (0,0,0,0))
    c = 0
    for i, line in enumerate(lines):
        # add each card on one by one
        for j, stop in enumerate(sorted(line.locked_stops)):
            # get its image (randomly rotated)
            angle = random.uniform(0, MAX_ROTATION)
            if c % 2 == 0:
                angle = -angle
            c += 1
            card_image = stop.image(observer).rotate(
                degrees(angle), expand=True)
            # paste it onto the image
            coordinates = (COLLECTION_SPACING + int(0.5*WIDTH) + i*(COLLECTION_SPACING + WIDTH),
                            COLLECTION_SPACING + j*VISIBLE_HEIGHT + int(0.5*HEIGHT))
            # paste relative to the center
            collection.paste(card_image, (coordinates[0] - int(
                0.5*card_image.width), coordinates[1] - int(0.5*card_image.height)), card_image)
    # return complete image
    return collection