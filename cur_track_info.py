import dbus_mpris.core as mpris_core
from typing import Any, List, Dict, Tuple
from consolemenu import SelectionMenu
import logging
import dbus_mpris.helpers as helpers

logger = logging.getLogger(__name__)


def print_track_info(
    player_metadata: Dict[str, Any], player_pos: int, playback_status: str
):
    """Formats and prints track info to the console"""
    try:
        player_pos_hhmmss = helpers.to_HHMMSS(player_pos)
        title = player_metadata["xesam:title"]
        length = int(player_metadata["mpris:length"])
        length_s = helpers.to_HHMMSS(length)
        print(f"{title}")
        print(f"{player_pos_hhmmss} of {length_s}")
        print(playback_status)
    except Exception as e:
        logger.error(e)


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
        track_meta, track_pos, playback_status = mpris_core.get_cur_track_info(player)
        print_track_info(track_meta, track_pos, playback_status)
    except Exception as err:
        logger.error(err)
