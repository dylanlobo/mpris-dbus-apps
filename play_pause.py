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
        player_instance_names = mpris_core.get_running_player_instance_names()
        if len(player_instance_names) == 0:
            logger.error("No mpris enabled players are running")
            exit()
        # select a player to connect to
        selected_player_name = ""
        player_names = list(player_instance_names.keys())
        if len(player_instance_names) == 1:
            selected_player_name = player_names[0]
        else:
            selected_player_name = helpers.select_player_instance_name(
                list(player_instance_names.keys())
            )
        player = mpris_core.get_player(
            selected_player_name, player_instance_names[selected_player_name]
        )
        player.PlayPause()
    except Exception as err:
        logging.error(err)
