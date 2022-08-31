"""Convenience wrappers for DBbus MPRIS core functionality"""
import dbus
from dbus import DBusException
from typing import Any, List, Dict, Tuple
from consolemenu import SelectionMenu
import logging

logger = logging.getLogger(__name__)


def get_running_player_instance_names() -> Dict[str, str]:
    """Retrieves media player instances names of currently running
    MPRIS D-Bus enabled players, from the dbus SessionBus.
    Returns a dictionary. The dictionary key is the unqualified
    player instance name and value is the fully qualified player name."""

    running_players = {}
    mediaPlayer_prefix = "org.mpris.MediaPlayer2"
    mediaPlayer_prefix_len = len(mediaPlayer_prefix)
    for service in dbus.SessionBus().list_names():
        if mediaPlayer_prefix in service:
            service_suffix = service[mediaPlayer_prefix_len + 1 :]
            running_players[service_suffix] = str(service)
    return running_players


def get_player(player_name: str, fq_player_name: str) -> dbus.Interface:
    """Returns a dbus object instance of the specified player instance.
    Arguments
    player_name -- a string containing the name a running player instance. Eg. rhythmbox
    fq_player_name -- a string containing the fully qualified name of a running player instance.
    Eg. org.mpris.MediaPlayer2.rhythmbox
    Retrun a dbus.Interface("org.mpris.MediaPlayer2.Player") instance of the specified player instance name.
    """
    bus = dbus.SessionBus()
    proxy = None
    try:
        proxy = bus.get_object(fq_player_name, "/org/mpris/MediaPlayer2")
    except DBusException as e:
        logger.error(f"Unable to retrieve the {fq_player_name} proxy from dbus.")
        raise Exception(
            f"Unable to connect to {player_name}, check if {player_name} it is running."
        )
    player = dbus.Interface(proxy, dbus_interface="org.mpris.MediaPlayer2.Player")
    return player


def select_player_instance_name(player_names: List[str]) -> str:
    """Presents the user with an interactive console to select a player
    instance.
    Arguments:
    player_names -- a list containing the names of the player instances.
    Returns a string containing the player name selected by the user"""

    if not isinstance(player_names, list):
        raise TypeError("player_names is not a list")

    selection = SelectionMenu.get_selection(
        title="Select a player to connect to:",
        strings=player_names,
        show_exit_option=False,
    )
    return player_names[selection]


def get_selected_player():
    """Returns a dbus object instance of the user selected player instance."""

    player_instance_names = get_running_player_instance_names()
    if len(player_instance_names) == 0:
        logger.error("No mpris enabled players are running")
        return None
    # select a player to connect to
    selected_player_name = ""
    player_names = list(player_instance_names.keys())
    if len(player_instance_names) == 1:
        selected_player_name = player_names[0]
    else:
        selected_player_name = select_player_instance_name(
            list(player_instance_names.keys())
        )
    player = get_player(
        selected_player_name, player_instance_names[selected_player_name]
    )
    return player


def get_cur_track_info(player: dbus.Interface) -> Tuple[str, str, str]:
    """Retrieves informtion about the currently selected track in the
    specifed player instance.
    Arguments
    player -- a dbus.Interface("org.mpris.MediaPlayer2.Player") instance of the selected player instance name.
    Return a tuple of strings containing the player's Metadata, Postion and PlaybackStatus
    """
    player_properties = dbus.Interface(
        player, dbus_interface="org.freedesktop.DBus.Properties"
    )
    player_metadata = player_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
    player_pos = player_properties.Get("org.mpris.MediaPlayer2.Player", "Position")
    playback_status = player_properties.Get(
        "org.mpris.MediaPlayer2.Player", "PlaybackStatus"
    )
    #    return player_metadata["xesam:title"]
    return (player_metadata, player_pos, playback_status)
