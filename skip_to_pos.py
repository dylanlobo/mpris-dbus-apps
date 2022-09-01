"""
Skips from the current postion to the time offset, 
specified by HH:MM:SS format, in the currently playing track.
"""
from ast import arg
from typing import Tuple
import dbus_mpris.core as mpris_core
import dbus_mpris.helpers as helpers
import argparse
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


def get_cmd_line_args() -> Tuple[helpers.Direction, int]:
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
    direction = helpers.Direction.FORWARD
    if arguments.r:
        direction = helpers.Direction.REVERSE
    time_in_ms = helpers.to_microsecs(arguments.time)
    return direction, time_in_ms


if __name__ == "__main__":
    try:
        player = mpris_core.get_selected_player()
        if player is None:
            logger.error("No mpris enabled players are running")
            exit()
        track_meta, track_pos, playback_status = mpris_core.get_cur_track_info(player)
        if playback_status == "Stopped":
            logger.error("The selected player is currently stopped")
            exit()
        elif playback_status == "Playing":
            player.Pause()
        direction, time_in_ms = get_cmd_line_args()
        player.Seek(time_in_ms * direction)
        player.Play()

    except Exception as err:
        logging.error(err)
