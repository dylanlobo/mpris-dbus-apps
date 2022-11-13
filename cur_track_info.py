import argparse
import logging
from typing import Dict, Any

import lib.dbus_mpris.helpers as mpris_helpers
from lib.dbus_mpris.core import PlayerFactory

logger = logging.getLogger(__name__)


def print_track_info(
    player_metadata: Dict[str, Any], player_pos: int, playback_status: str
):
    """Formats and prints track info to the console"""
    try:
        player_pos_hhmmss = mpris_helpers.to_HHMMSS(player_pos)
        title = player_metadata["xesam:title"]
        length = int(player_metadata["mpris:length"])
        length_s = mpris_helpers.to_HHMMSS(length)
        print(f"{title}")
        print(f"{player_pos_hhmmss} of {length_s}")
        print(playback_status)
    except Exception as e:
        logger.error(e)


def get_cmd_line_args():
    # Set up command line argument processing
    parser = argparse.ArgumentParser(
        description=(
            "Prints simplifed information about the current track of the selected player instance."
            "If multiple player instances are running, the user is presented with a selection menu."
        )
    )
    arguments = parser.parse_args()
    return arguments


if __name__ == "__main__":
    args = get_cmd_line_args()
    try:
        running_player_names = PlayerFactory.get_running_player_names()
        if not running_player_names:
            print("No mpris enabled players are running")
            exit()
        player = mpris_helpers.get_selected_player(running_player_names)
        if player is None:
            logger.error("No mpris enabled players are running")
            exit()
        print_track_info(player.metadata, player.position, player.playback_status)
    except Exception as err:
        logger.error(err)
