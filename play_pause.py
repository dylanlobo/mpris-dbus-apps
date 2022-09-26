"""Toggles the play/pause state of the selected player instance"""
import dbus_mpris.helpers as mpris_helpers
from dbus_mpris.core import Player
import argparse
import logging

logger = logging.getLogger(__name__)


def get_cmd_line_args():
    # Set up command line argument processing
    parser = argparse.ArgumentParser(
        description=(
            "Toggles the play/pause state of the selected player instance. "
            "If multiple player instances are running, the user is presented with a selection menu."
        )
    )
    arguments = parser.parse_args()
    return arguments


if __name__ == "__main__":
    try:
        running_player_names = Player.get_running_player_names()
        if not running_player_names:
            print("No mpris enabled players are running")
            exit()
        player = mpris_helpers.get_selected_player(running_player_names)
        player.play_pause()
    except Exception as err:
        logging.error(err)
