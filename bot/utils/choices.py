from discord import OptionChoice
from tramopoly import getAllActionCards, ActionType, getAllLines, getAllSpecialAbilities, getAllZones

STANDARD_ACTIONS = [OptionChoice(action.title, action.code)
                    for action in getAllActionCards()
                    if not action.type == ActionType.CURSE]

CURSES = [OptionChoice(action.title, action.code)
          for action in getAllActionCards()
          if action.type == ActionType.CURSE]

LINES = [OptionChoice(line.emoji + " " + line.colour + " line", line.colour)
         for line in getAllLines()]

SPECIAL_ABILITIES = [OptionChoice(special.name, special.code)
                     for special in getAllSpecialAbilities()]

ZONES = [
    OptionChoice(f"Zone {zone.number}", zone.number)
    for zone in getAllZones()
]