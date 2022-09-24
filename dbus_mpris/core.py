"""Convenience wrappers for DBbus MPRIS core functionality"""
import dbus
import re
import logging
from dbus import DBusException
from typing import Any, List, Dict, Tuple
from consolemenu import SelectionMenu
from functools import lru_cache, cached_property

logger = logging.getLogger(__name__)


@lru_cache()
def is_object_path_valid(path: str) -> bool:
    """Whether this is a valid object path.
    .. see also:: https://dbus.freedesktop.org/doc/dbus-specification.html#message-protocol-marshaling-object-path
    :param path: The object path to validate.
    :returns: Whether the object path is valid.
    """
    _path_re = re.compile(r"^[A-Za-z0-9_]+$")
    if not isinstance(path, str):
        return False

    if not path:
        return False

    if not path.startswith("/"):
        return False

    if len(path) == 1:
        return True

    for element in path[1:].split("/"):
        if _path_re.search(element) is None:
            return False

    return True


class Player:
    """A convience class whose object instances encapsulates
    an mpris player object and exposes a subset of
    the org.mpris.MediaPlayer2.Player interface."""

    @staticmethod
    def get_running_player_names() -> Dict[str, str]:
        """Retrieves media player instances names of currently running
        MPRIS D-Bus enabled players, from the dbus SessionBus.
        returns: a dictionary. The dictionary key is the unqualified
        player instance name and value is the fully qualified player name."""

        running_players = {}
        mediaPlayer_prefix = "org.mpris.MediaPlayer2"
        mediaPlayer_prefix_len = len(mediaPlayer_prefix)
        for service in dbus.SessionBus().list_names():
            if mediaPlayer_prefix in service:
                service_suffix = service[mediaPlayer_prefix_len + 1 :]
                running_players[service_suffix] = str(service)
        return running_players

    def __init__(self, mpris_player_name, ext_player_name) -> None:
        self._name = mpris_player_name
        self._ext_name = ext_player_name
        bus = dbus.SessionBus()
        proxy = None
        try:
            self._proxy = bus.get_object(self._name, "/org/mpris/MediaPlayer2")
        except DBusException as e:
            logger.error(f"Unable to retrieve the {self._name} proxy from dbus.")
            raise Exception(
                f"Unable to connect to {self._ext_name}, check if {self._ext_name} it is running."
            )
        self._player = dbus.Interface(
            self._proxy, dbus_interface="org.mpris.MediaPlayer2.Player"
        )
        self._player_properties = dbus.Interface(
            self._player, dbus_interface="org.freedesktop.DBus.Properties"
        )

    def Play(self) -> None:
        self.mpris_player.Play()

    def PlayPause(self) -> None:
        self.mpris_player.PlayPause()

    def Pause(self) -> None:
        self.mpris_player.Pause()

    def Stop(self) -> None:
        self.mpris_player.Stop()

    def Seek(self, offset: int) -> None:
        self.mpris_player.Seek(offset)

    def SetPosition(self, to_position: int) -> None:
        id = self.trackid
        if is_object_path_valid(id):
            self.mpris_player.SetPosition(id, to_position)
        else:
            logger.warning(f"The trackid returned by {self.ext_name} is not valid.")
            logger.debug(
                "Unable to use SetPosition(trackid,postion), due to invalid trackid value."
            )
            logger.debug(f"Attempting to use Seek() to set the requested postion.")
            cur_pos = self.position
            seek_to_position = to_position - cur_pos
            # self.Seek(to_microsecs("99:59:59") * -1)
            # self.Seek(to_position)
            self.Seek(seek_to_position)

    def Get(self, interface_name: str, property_name: str) -> Any:
        return self.mpris_player_properties.Get(interface_name, property_name)

    @property
    def mpris_player(self) -> dbus.Interface:
        return self._player

    @property
    def mpris_player_properties(self) -> dbus.Interface:
        return self._player_properties

    @property
    def name(self) -> str:
        return self._name

    @property
    def ext_name(self) -> str:
        return self._ext_name

    @property
    def playback_status(self) -> str:
        return self.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")

    @property
    def position(self) -> int:
        return self.Get("org.mpris.MediaPlayer2.Player", "Position")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.Get("org.mpris.MediaPlayer2.Player", "Metadata")

    @property
    def trackid(self) -> str:
        return self.metadata["mpris:trackid"]

    @cached_property
    def can_control(self) -> bool:
        return self.Get("org.mpris.MediaPlayer2.Player", "CanControl")

    @cached_property
    def can_seek(self) -> bool:
        return self.Get("org.mpris.MediaPlayer2.Player", "CanSeek")

    @cached_property
    def can_pause(self) -> bool:
        return self.Get("org.mpris.MediaPlayer2.Player", "CanPause")

    @cached_property
    def can_play(self) -> bool:
        return self.Get("org.mpris.MediaPlayer2.Player", "CanPlay")


class NoValidMprisPlayers(Exception):
    pass


###################################################################################################
# def get_cur_track_info(player: dbus.Interface) -> Tuple[str, str, str]:
#    """Retrieves informtion about the currently selected track in the
#    specifed player instance.
#    Arguments
#    player -- a dbus.Interface("org.mpris.MediaPlayer2.Player") instance of the selected player instance name.
#    Return a tuple of strings containing the player's Metadata, Postion and PlaybackStatus
#    """
#    player_properties = dbus.Interface(
#        player, dbus_interface="org.freedesktop.DBus.Properties"
#    )
#    player_metadata = player_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
#    player_pos = player_properties.Get("org.mpris.MediaPlayer2.Player", "Position")
#    playback_status = player_properties.Get(
#        "org.mpris.MediaPlayer2.Player", "PlaybackStatus"
#    )
#    #    return player_metadata["xesam:title"]
#    return (player_metadata, player_pos, playback_status)
#
#
# def get_running_player_instance_names() -> Dict[str, str]:
#    """Retrieves media player instances names of currently running
#    MPRIS D-Bus enabled players, from the dbus SessionBus.
#    Returns a dictionary. The dictionary key is the unqualified
#    player instance name and value is the fully qualified player name."""
#
#    running_players = {}
#    mediaPlayer_prefix = "org.mpris.MediaPlayer2"
#    mediaPlayer_prefix_len = len(mediaPlayer_prefix)
#    for service in dbus.SessionBus().list_names():
#        if mediaPlayer_prefix in service:
#            service_suffix = service[mediaPlayer_prefix_len + 1 :]
#            running_players[service_suffix] = str(service)
#    return running_players
#
#
# def get_player(player_name: str, fq_player_name: str) -> dbus.Interface:
#    """Returns a dbus object instance of the specified player instance.
#    Arguments
#    player_name -- a string containing the name a running player instance. Eg. rhythmbox
#    fq_player_name -- a string containing the fully qualified name of a running player instance.
#    Eg. org.mpris.MediaPlayer2.rhythmbox
#    Retrun a dbus.Interface("org.mpris.MediaPlayer2.Player") instance of the specified player instance name.
#    """
#    bus = dbus.SessionBus()
#    proxy = None
#    try:
#        proxy = bus.get_object(fq_player_name, "/org/mpris/MediaPlayer2")
#    except DBusException as e:
#        logger.error(f"Unable to retrieve the {fq_player_name} proxy from dbus.")
#        raise Exception(
#            f"Unable to connect to {player_name}, check if {player_name} it is running."
#        )
#    player = dbus.Interface(proxy, dbus_interface="org.mpris.MediaPlayer2.Player")
#    return player
#
#
# def select_player_instance_name(player_names: List[str]) -> str:
#    """Presents the user with an interactive console to select a player
#    instance.
#    Arguments:
#    player_names -- a list containing the names of the player instances.
#    Returns a string containing the player name selected by the user"""
#
#    if not isinstance(player_names, list):
#        raise TypeError("player_names is not a list")
#
#    selection = SelectionMenu.get_selection(
#        title="Select a player to connect to:",
#        strings=player_names,
#        show_exit_option=False,
#    )
#    return player_names[selection]
#
#
# def get_selected_player():
#    """Returns a dbus object instance of the user selected player instance."""
#
#    player_instance_names = get_running_player_instance_names()
#    if len(player_instance_names) == 0:
#        return None
#    # select a player to connect to
#    selected_player_name = ""
#    player_names = list(player_instance_names.keys())
#    if len(player_instance_names) == 1:
#        selected_player_name = player_names[0]
#    else:
#        selected_player_name = select_player_instance_name(
#            list(player_instance_names.keys())
#        )
#    player = get_player(
#        selected_player_name, player_instance_names[selected_player_name]
#    )
#    return player
#
