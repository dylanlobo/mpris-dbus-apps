"""
Helper functions for mpris-dbus-apps
"""

from pprint import pprint
import re
import logging
import os
import json
from lib.dbus_mpris.core import (
    PlayerCreationError,
    NoValidMprisPlayersError,
    Player,
    PlayerFactory,
)
from enum import IntEnum
from functools import lru_cache
from consolemenu import SelectionMenu
from typing import List, Dict, Tuple, TextIO
import lib.yt_ch as youtube_chapters

logger = logging.getLogger(__name__)


class Direction(IntEnum):
    FORWARD = 1
    REVERSE = -1


def is_player_useable(player: Player) -> bool:
    if player.can_control and player.can_seek:
        return True
    return False


def get_player(player_name: str, running_players: Dict[str, str]) -> Player:
    """Returns a wrapped dbus mpris object instance of the specified player instance.

    :param player_name: a string containing the name a running player instance.
        Eg. rhythmbox
    :param running_players: a dictionary containing running player names.
        The key is the unqualified player instance name and the value is
        the fully qualified player name.
        Eg. {"rhythmbox","org.mpris.MediaPlayer2.rhythmbox"}
    :returns: a dbus.Interface("org.mpris.MediaPlayer2.Player") instance of the
        specified player instance name.
    """
    mpris_player_name = running_players[player_name]
    player = None
    try:
        player = PlayerFactory.get_player(mpris_player_name, player_name)
    except PlayerCreationError as e:
        logger.error(e)
        raise e
    return player


@lru_cache
def to_microsecs(time_str: str) -> int:
    """Converts time specified by the string HH:MM:SS into microseconds.

    Arguments
    time_str is a string.  The maximum value is 99:59:59. The minimum value is 00:00:00
    Returns
    An interger value of the converted time in microseconds
    """

    # Setup the regex expression that will validate the time format
    m = re.search("^[0-9][0-9]:[0-5][0-9]:[0-5][0-9]$", time_str)
    if m is None:
        raise ValueError(
            "Invalid time format. The valid format is HH:MM:SS."
            "The maximum value is 99:59:59."
            "The minimum value is 00:00:00"
        )
    parts = time_str.split(":")
    int_parts = [int(s) for s in parts]
    hours, mins, secs = int_parts
    total_mins = (hours * 60) + mins
    mins_in_microsecs = total_mins * 60000000
    total_microsecs = mins_in_microsecs + (secs * 1000000)
    return total_microsecs


def to_HHMMSS(microsecs: int) -> str:
    """Converts time specifed in microseconds to HH:MM:SS time format.
    The maximum input value is 359999000000, which is equvalent to
    99:59:59 in HH:MM:SS format.

    Arguments
    microsecs is an integer, -ve input values are converted to +ve values
    Returns a string in HH:MM:SS time format.
    """

    abs_microsecs = abs(microsecs)
    if abs_microsecs > 359999000000:
        raise ValueError("Max absolute value of microsecs is 359999000000")
    total_secs = int(abs_microsecs / 1000000)
    total_minutes = int(total_secs / 60)
    left_over_secs = total_secs % 60
    hours = int(total_minutes / 60)
    minutes = int(total_minutes % 60)
    seconds = left_over_secs
    sec_s = f"{seconds}" if seconds > 9 else f"0{seconds}"
    min_s = f"{minutes}" if minutes > 9 else f"0{minutes}"
    hr_s = f"{hours}" if hours > 9 else f"0{hours}"
    return f"{hr_s}:{min_s}:{sec_s}"


def chapters_json_to_py(ch_json: str) -> Tuple[str, Dict[str, str]]:
    chapters = {}
    title = "No Title"
    try:
        json_dict = json.loads(ch_json)
    except json.JSONDecodeError as e:
        logger.critical(f"Chapters content is not a valid JSON document. {e}")
        raise ValueError(f"Chapters content is not a valid JSON document.{e}")

    if json_dict["title"]:
        title = json_dict["title"]
    else:
        title = "Chapters"
    if json_dict["chapters"]:
        chapters = json_dict["chapters"]
    else:
        chapters = {}
    return title, chapters


def chapters_py_to_json(title: str, chapters: Dict[str, str]) -> str:
    chapters_dict = {"title": None, "chapters": None}
    title = title if title else "title"
    chapters_dict["title"] = title
    chapters_dict["chapters"] = chapters
    return json.dumps(chapters_dict, indent=4)


def load_chapters_file(chapters_file: str | TextIO) -> Tuple[str, Dict[str, str]]:
    if not chapters_file:
        raise FileNotFoundError()
    chapters = {}
    title = "Chapters"
    chapters_json = ""
    if isinstance(chapters_file, str):
        if os.path.isfile(chapters_file) is False:
            logger.error(f"{chapters_file} does not exist")
            raise FileNotFoundError(f"{chapters_file} does not exist")
        chapters_file = open(chapters_file, "r")
    with chapters_file:
        chapters_json = chapters_file.read()

    (title, chapters) = chapters_json_to_py(chapters_json)
    return title, chapters


def save_chapters_file(
    chapters_file: str | TextIO, title: str, chapters: Dict[str, str]
):
    if not chapters_file:
        raise FileNotFoundError()
    json_str = chapters_py_to_json(title=title, chapters=chapters)
    if isinstance(chapters_file, str):
        if os.path.isfile(chapters_file) is False:
            logger.error(f"{chapters_file} does not exist")
            raise FileNotFoundError(f"{chapters_file} does not exist")
        chapters_file = open(chapters_file, "w")
    with chapters_file:
        chapters_file.write(json_str)


def load_chapters_from_youtube(video: str):
    chapters = {}
    title = "Chapters"
    chapters_json = ""
    _, chapters_json = youtube_chapters.get_chapters_json(video)
    (title, chapters) = chapters_json_to_py(chapters_json)
    return title, chapters


def get_selected_player(running_players: Dict[str, str]) -> Player:
    """Select a player to connect to.
    :param running_players:  A dictionary containing names of running
    mpris enabled players.The key is the unqualified player instance name
    and value is the fully qualified player instance name.
    :returns: A valid Player instance on successful completion.
    :raises: NoValidMprisPlayersError exception if no valid MPRIS enable players
    are available.
    """
    if not running_players:
        raise ValueError("running_players is empty.")

    selected_player_name = ""
    player: Player
    player_names = list(running_players.keys())
    if len(player_names) == 1:
        selected_player_name = player_names[0]
    else:
        selected_player_name = user_select_player(player_names)

    player = get_player(selected_player_name, running_players)

    while not is_player_useable(player):
        player_names.remove(selected_player_name)
        if not player_names:
            msg = f"{selected_player_name} is not useable. \
            No other mpris enabled players are currently running."
            logger.error(msg)
            raise NoValidMprisPlayersError(msg)

        if user_try_another_player():
            selected_player_name = user_select_player(player_names)
            player = get_player(selected_player_name, running_players)
        else:
            raise NoValidMprisPlayersError
    return player


def user_try_another_player() -> bool:
    """Interactive prompt informing the user that their existing player
    selection is not valid and requesting the user to choose a different player"""
    while True:
        answer = input(
            "The selected player does not implement required MPRIS functionality.\n \
                Select another player? Yes[y] or "
            "No[n] default[y]: "
        )
        answer = answer.lower()
        if answer in ("", "y", "yes"):
            return True
        elif answer in ("n", "no"):
            return False


def user_select_player(player_names: List[str]) -> str:
    """Presents the user with an interactive console to select a mpris enabled player
    instance.

    :param: player_names -- a list containing the names of the mpris enabled player \
        instances.
    :returns: a string containing the player name selected by the user"""

    if not isinstance(player_names, list):
        raise TypeError("player_names is not a list")

    selection = SelectionMenu.get_selection(
        title="Select a player to connect to:",
        strings=player_names,
        show_exit_option=False,
    )
    return player_names[selection]
