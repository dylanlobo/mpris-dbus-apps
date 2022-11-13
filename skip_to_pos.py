"""
Skips from the current postion to the time offset,
specified by HH:MM:SS format, in the currently playing track.
"""
from typing import Tuple
from lib.dbus_mpris.core import PlayerFactory
import lib.dbus_mpris.helpers as mpris_helpers
import argparse
import logging

logger = logging.getLogger(__name__)


def get_cmd_line_args() -> Tuple[mpris_helpers.Direction, int]:
    # Set up command line argument processing
    parser = argparse.ArgumentParser(
        description=(
            "Skips from the current postion to the time offset,"
            " specified by HH:MM:SS format, in the currently playing track.  "
            "Skips forward by default."
            " Skips backwards when the -r flag is specified "
            " Example: python skip_to_pos.py 03:43:10"
        )
    )
    parser.add_argument(
        "-r",
        action="store_true",
        required=False,
        help="Skips backwards by the specified time.",
    )
    parser.add_argument(
        "time", action="store", help="Specfiy the time in HH:MM:SS format."
    )
    arguments = parser.parse_args()
    direction = mpris_helpers.Direction.FORWARD
    if arguments.r:
        direction = mpris_helpers.Direction.REVERSE
    time_in_ms = mpris_helpers.to_microsecs(arguments.time)
    return direction, time_in_ms


if __name__ == "__main__":
    try:
        direction, time_in_ms = get_cmd_line_args()
        running_player_names = PlayerFactory.get_running_player_names()
        if not running_player_names:
            print("No mpris enabled players are running")
            exit()
        player = mpris_helpers.get_selected_player(running_player_names)
        if player is None:
            logger.error("No mpris enabled players are running")
            exit()
        player.seek(time_in_ms * direction)

    except Exception as err:
        logging.error(err)
