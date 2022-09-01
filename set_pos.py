"""
Sets the playback time position, in the currently playing track.
"""

import dbus_mpris.core as mpris_core
import dbus_mpris.helpers as helpers
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
    return helpers.to_microsecs(time_str)


if __name__ == "__main__":
    try:
        micro_secs = get_cmd_line_args()
        player = mpris_core.get_selected_player()
        if player is None:
            logger.error("No mpris enabled players are running")
            exit()
        track_meta, track_pos, playback_status = mpris_core.get_cur_track_info(player)
        player.SetPosition(track_meta["mpris:trackid"], micro_secs)

    except Exception as err:
        logger.error(err)
