from tramopoly import Stop, Team, Line, Action, Special, Game, drawMap, ActionType, Card, Challenge, Zone
from tramopoly.card_images import IconType, drawCollection, CollectionStyle
from tramopoly.data import getIconData, getTeamColour, getActionTypeData
from discord import Embed, EmbedField, File
from utils.data import getEmojiCode, mention, mentionPossessive, countdownTo, getSelfie, getSelfieFilename, exactTime
from datetime import datetime
from PIL.Image import Image
from io import BytesIO

GRAY = "b5bac1"
ERROR = "ff5a47"


def embed_stop(stop: Stop, observer: Team | None = None) -> tuple[Embed, list[File]]:
    # determine icon
    icon_type = stop.map_icon(observer)
    # determine colour
    if icon_type in [IconType.CLAIMED_YOU, IconType.CLAIMED_OTHER, IconType.LOCKED_YOU, IconType.LOCKED_OTHER]:
        # use the colour of the team that owns it...
        colour = getTeamColour(stop.owner.colour)
    elif icon_type != IconType.NONE:
        icon_data = getIconData(icon_type)
        # use the colour of the icon
        colour = icon_data["colour"]
    else:
        # use discord grey
        colour = GRAY
    # attach image
    filename = getFilename()
    return (
        Embed(
            colour=int(colour, 16),
            image="attachment://"+filename
        ),
        [getFile(stop.full_image(observer), filename)]
    )


def embed_line(line: Line, observer: Team | None = None) -> tuple[Embed, list[File]]:
    if not line.claimed:
        return (
            Embed(
                colour=int(line.hex_colour, 16),
                title=f"The {line.colour} line has not been claimed."
            ),
            []
        )
    # attach image
    filename = getFilename()
    return (
        Embed(
            colour=int(getTeamColour(line.owner.colour), 16),
            image="attachment://"+filename,
            title=f"{mention(line.owner, observer, True, False)} own the {
                line.colour} line."
        ),
        [getFile(line.image(observer), filename)]
    )


def embed_challenges(stop: Stop) -> tuple[Embed, list[File]]:
    return (
        Embed(
            title=f"Challenges at {stop.name}",
            fields=[
                EmbedField(
                    name=f"{getEmojiCode('challenge_'+str(i+1))
                            } {challenge.title}",
                    value=formatChallengeContent(challenge),
                    inline=True
                ) for i, challenge in enumerate(stop.challenges)
            ],
            colour=int(getIconData(IconType.CHALLENGE)["colour"], 16)
        ),
        []
    )

def formatChallengeContent(challenge: Challenge):
    authors = challenge.authors
    author_text = " *Written by "
    if not authors:
        return challenge.content
    for author in authors:
        author_text += author + ", "
    author_text = author_text[:-2] + ".*"
    return challenge.content + author_text

def embed_current_challenge(team: Team) -> tuple[Embed, list[File]]:
    current_challenge = team.current_challenge
    if team.in_veto:
        return (
            Embed(
                title=f"{mention(team, team, True, False)
                         } are currently in a veto period.",
                description=f"After failing to complete {current_challenge.title} at {current_challenge.location.name}, {
                    mention(team, team, False, False)} must wait for a veto period to end {countdownTo(team.veto_end)} to start any new challenges or board any trams. ({exactTime(team.veto_end)})",
                colour=int(ERROR, 16),
            ),
            []
        )
    elif not team.in_challenge:
        return (
            Embed(
                colour=int(getIconData(IconType.CHALLENGE)["colour"], 16),
                title=f"{mention(team, team, True, False)
                         } are not currently in a challenge or veto period."
            ),
            []
        )
    else:
        return (
            Embed(
                title=f"{mentionPossessive(team, team, True, False)} current challenge at {
                    current_challenge.location.name}",
                fields=[
                    EmbedField(
                        name=f"{getEmojiCode('challenge_'+str(current_challenge.location.challenges.index(current_challenge) + 1))
                                } {current_challenge.title}",
                        value=formatChallengeContent(current_challenge),
                        inline=True
                    )
                ],
                colour=int(getIconData(IconType.CHALLENGE)["colour"], 16),
            ),
            []
        )


def embed_action(action: Action) -> tuple[Embed, list[File]]:
    # attach image
    filename = getFilename()
    return (
        Embed(
            colour=int(getActionTypeData(action.type)["colour"], 16),
            image="attachment://"+filename
        ),
        [getFile(action.image(), filename)]
    )


def embed_played_action(action: Action, observer: Team | None = None, args: tuple[Card] | Card = ()) -> tuple[Embed, list[File]]:
    if not isinstance(args, tuple):
        args = tuple([args])
    # attach image
    all_cards = list(action.counter_chain)
    all_cards.extend(args)
    filename = getFilename()
    return (
        Embed(
            colour=int(getActionTypeData(action.type)["colour"], 16),
            image="attachment://"+filename
        ),
        [getFile(drawCollection(
            all_cards, CollectionStyle.HORIZONTAL, observer), filename)]
    )


def embed_special(special: Special) -> tuple[Embed, list[File]]:
    # attach image
    filename = getFilename()
    return (
        Embed(
            colour=int(getIconData(IconType.SPECIAL_ABILITY)["colour"], 16),
            image="attachment://"+filename
        ),
        [getFile(special.image(), filename)]
    )


def embed_map(game: Game | None = None,  observer: Team | None = None) -> tuple[Embed, list[File]]:
    # create file
    filename = getFilename()
    # all observer nonsense is handled by library
    return (
        Embed(
            colour=int(GRAY, 16),
            image="attachment://"+filename
        ),
        [getFile(drawMap(game, observer), filename)]
    )


def embed_line_claim_options(team: Team, line: Line) -> tuple[Embed, list[File]]:
    # create file
    filename = getFilename()
    return (
        Embed(
            title=f"{mentionPossessive(team, team, True, False)
                     } unlocked stops on the {line.colour} line",
            colour=int(line.hex_colour, 16),
            image="attachment://"+filename
        ),
        [getFile(drawCollection(team.free_stops_on_line(line),
                 CollectionStyle.HORIZONTAL, team), filename)]
    )


def embed_unlocked_stops(team: Team, observer: Team | None = None) -> tuple[Embed, list[File]]:
    if team.claimed_unlocked_stops:
        # create file
        filename = getFilename()
        return (
            Embed(
                title=f"{mentionPossessive(team, observer, True, False)
                         } unlocked stops",
                colour=int(getTeamColour(team.colour), 16),
                image="attachment://"+filename
            ),
            [getFile(team.unlocked_stops_image(observer), filename)]
        )
    else:
        return (
            Embed(
                colour=int(getTeamColour(team.colour), 16),
                title=f"{mention(team, observer, True, False)
                         } do not own any unlocked stops."
            ),
            []
        )


def embed_locked_lines(team: Team, observer: Team | None = None) -> tuple[Embed, list[File]]:
    if team.claimed_lines:
        # create file
        filename = getFilename()
        return (
            Embed(
                title=f"{mentionPossessive(team, observer, True, False)
                         } completed lines",
                colour=int(getTeamColour(team.colour), 16),
                image="attachment://"+filename
            ),
            [getFile(team.locked_lines_image(observer), filename)]
        )
    else:
        return (
            Embed(
                colour=int(getTeamColour(team.colour), 16),
                title=f"{mention(team, observer, True, False)
                         } do not own any completed lines."
            ),
            []
        )

# TODO: EMBED DISCARDED SECRETS :)


def embed_discarded_secrets(team: Team, discarded_secrets: list[Stop], observer: Team | None = None):
    # create file
    filename = getFilename()
    return (
        Embed(
            colour=int(getTeamColour(team.colour), 16),
            image="attachment://"+filename
        ),
        [getFile(drawCollection(discarded_secrets,
                 CollectionStyle.HORIZONTAL, observer), filename)]
    )


def embed_available_actions(team: Team, observer: Team | None = None) -> tuple[Embed, list[File]]:
    if team.available_actions:
        # create file
        filename = getFilename()
        return (
            Embed(
                title=f"{mentionPossessive(team, observer, True, False)
                         } available action cards",
                colour=int(getTeamColour(team.colour), 16),
                image="attachment://"+filename
            ),
            [getFile(team.available_actions_image(), filename)]
        )
    else:
        return (
            Embed(
                colour=int(getTeamColour(team.colour), 16),
                title=f"{mention(team, observer, True, False)
                         } do not own any action cards."
            ),
            []
        )


def embed_available_starting_actions(team: Team) -> tuple[Embed, list[File]]:
    filename = getFilename()
    return (
        Embed(
            colour=int(getIconData(IconType.REWARD)["colour"], 16),
            image="attachment://"+filename
        ),
        [getFile(team.available_starting_actions_image(), filename)]
    )


def embed_available_curses(team: Team) -> tuple[Embed, list[File]]:
    filename = getFilename()
    return (
        Embed(
            colour=int(getActionTypeData(ActionType.CURSE)["colour"], 16),
            image="attachment://"+filename
        ),
        [getFile(team.available_curses_image(), filename)]
    )


def embed_zone_options(team: Team, action_code: str) -> tuple[Embed, list[File]]:
    filename = getFilename()
    return (
        Embed(
            colour=int(getActionTypeData(
                Action(action_code).type)["colour"], 16),
            image="attachment://"+filename
        ),
        [getFile(drawCollection(team.getActionsByCode(action_code), CollectionStyle.HORIZONTAL, team), filename)]
    )


def embed_counter_options(team: Team, action: Action) -> tuple[Embed, list[File]]:
    filename = getFilename()
    return (
        Embed(
            colour=int(getIconData(IconType.REWARD)["colour"], 16),
            image="attachment://"+filename
        ),
        [getFile(team.counter_options_image(action), filename)]
    )


def embed_secrets(team: Team) -> tuple[Embed, list[File]]:
    if team.secrets:
        # create file
        filename = getFilename()
        return (
            Embed(
                colour=int(getIconData(IconType.SECRET)["colour"], 16),
                title=f"{mentionPossessive(
                    team, team, True, False)} secret cards",
                image="attachment://"+filename
            ),
            [getFile(team.secrets_image(), filename)]
        )
    else:
        return (
            Embed(
                colour=int(getIconData(IconType.SECRET)["colour"], 16),
                title=f"{mention(team, team, True, False)
                         } do not have any secret cards."
            ),
            []
        )


def embed_revealed_secrets(team: Team, observer: Team | None = None) -> tuple[Embed, list[File]]:
    if team.revealed_secrets:
        # create file
        filename = getFilename()
        return (
            Embed(
                colour=int(getIconData(IconType.SECRET)["colour"], 16),
                title=f"{mentionPossessive(
                    team, observer, True, False)} revealed secret cards",
                image="attachment://"+filename
            ),
            [getFile(team.revealed_secrets_image(), filename)]
        )
    else:
        return (
            Embed(
                colour=int(getIconData(IconType.SECRET)["colour"], 16),
                title=f"{mention(team, observer, True, False)
                         } do not have any revealed secret cards."
            ),
            []
        )


def embed_unrevealed_secrets(team: Team) -> tuple[Embed, list[File]]:
    if team.unrevealed_secrets:
        # create file
        filename = getFilename()
        return (
            Embed(
                colour=int(getIconData(IconType.SECRET)["colour"], 16),
                title=f"{mentionPossessive(
                    team, team, True, False)} unrevealed secret cards",
                image="attachment://"+filename
            ),
            [getFile(team.unrevealed_secrets_image(), filename)]
        )
    else:
        return (
            Embed(
                colour=int(getIconData(IconType.SECRET)["colour"], 16),
                title=f"{mention(team, team, True, False)
                         } do not have any unrevealed secret cards."
            ),
            []
        )


def embed_curses(team: Team, observer: Team | None = None) -> tuple[Embed, list[File]]:
    ongoing = team.ongoing_curses
    if ongoing or team.uncleared_curses:
        # create file
        filename = getFilename()
        return (
            Embed(
                title=f"{mentionPossessive(team, observer, True, False)
                         } current curses",
                colour=int(getActionTypeData(ActionType.CURSE)["colour"], 16),
                image="attachment://"+filename
            ),
            [getFile(team.current_curses_image(), filename)]
        )
    else:
        return (
            Embed(
                colour=int(getActionTypeData(ActionType.CURSE)["colour"], 16),
                title=f"{mention(team, observer, True, False)
                         } are not currently subject to any curses."
            ),
            []
        )


def embed_abilities(team: Team, observer: Team | None = None) -> tuple[Embed, list[File]]:
    if team.special_abilities:
        # create file
        filename = getFilename()
        return (
            Embed(
                title=f"{mentionPossessive(team, observer, True, False)
                         } special abilities",
                colour=int(getIconData(IconType.SPECIAL_ABILITY)
                           ["colour"], 16),
                image="attachment://"+filename
            ),
            [getFile(team.special_abilities_image(), filename)]
        )
    else:
        return (
            Embed(
                colour=int(getIconData(IconType.SPECIAL_ABILITY)
                           ["colour"], 16),
                title=f"{mention(team, observer, True, False)
                         } do not have any special abilities."
            ),
            []
        )


def embed_selfie(team: Team, challenge: Challenge) -> tuple[Embed, list[File]]:
    filename = getSelfieFilename(team, challenge)
    return (
        Embed(
            colour=int(getTeamColour(team.colour), 16),
            image="attachment://"+filename
        ),
        [getSelfie(team, challenge)]
    )


def embed_complaint(title: str, message: str) -> tuple[Embed, list[File]]:
    return (
        Embed(
            colour=int(ERROR, 16),
            title=title,
            description=message,
        ),
        []
    )


def embed_claim(stop: Stop, rewards: list[Card] | Card | None, observer: Team | None = None) -> tuple[Embed, list[File]]:
    cards = [stop]
    # determine if it's multiple or a single reward (inlcudes choice)
    if isinstance(rewards, list):
        cards.extend(rewards)
    elif rewards != None:
        cards.append(rewards)
    # attach image
    filename = getFilename()
    return (
        Embed(
            colour=int(getTeamColour(stop.owner.colour), 16),
            image="attachment://"+filename
        ),
        [getFile(drawCollection(cards, CollectionStyle.HORIZONTAL, observer), filename)]
    )


def embed_deck(zone: Zone) -> tuple[Embed, list[File]]:
    # attach image
    filename = getFilename()
    return (
        Embed(
            colour=int(getIconData(IconType.REWARD)["colour"], 16),
            image="attachment://"+filename,
            title=f"Zone {zone.number} deck"
        ),
        [getFile(drawCollection(zone.start_deck, CollectionStyle.HORIZONTAL), filename)]
    )


def getFilename() -> str:
    return str(datetime.now().timestamp()) + ".png"


def getFile(image: Image, filename: str) -> File:
    bytes = BytesIO()
    image.save(bytes, "PNG")
    bytes.seek(0)
    return File(bytes, filename)
