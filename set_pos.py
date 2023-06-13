"""
Sets the playback time position, in the currently playing track.
"""

from lib.dbus_mpris.player import PlayerFactory
import lib.dbus_mpris.helpers as mpris_helpers
import logging
import argparse

logger = logging.getLogger(__name__)


def get_cmd_line_args() -> int:
    """Returns the number of mircroseconds that was specified in the command line
    as time in HH:MM:SS format"""
    # Set up command line argument processing
    parser = argparse.ArgumentParser(
        description=(
            "Sets the current playback postion to the time offset,"
            " specified by HH:MM:SS format, in the currently playing track.  "
            " Example: python set_pos.py 03:43:10"
        )
    )
    parser.add_argument(
        "time", action="store", help="Specfiy the time in HH:MM:SS format."
    )
    arguments = parser.parse_args()
    time_str = arguments.time
    return mpris_helpers.to_microsecs(time_str)


if __name__ == "__main__":
    try:
        micro_secs = get_cmd_line_args()
        running_player_names = PlayerFactory.get_running_player_names()
        if not running_player_names:
            print("No mpris enabled players are running")
            exit()
        player = mpris_helpers.get_selected_player(running_player_names)
        if player is None:
            logger.error("No mpris enabled players are running")
            exit()
        player.set_position(micro_secs)

    except Exception as err:
        logger.error(err)
