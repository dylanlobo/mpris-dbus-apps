"""Toggles the play/pause state of the selected player instance"""
import dbus_mpris.core as mpris_core
import dbus_mpris.helpers as helpers
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
        player = mpris_core.get_selected_player()
        if player is None:
            logger.error("No mpris enabled players are running")
            exit()
        player.PlayPause()
    except Exception as err:
        logging.error(err)
