"""Convenience wrappers for DBbus MPRIS core functionality"""
import dbus
import re
import logging
from dbus import DBusException
from typing import Any, Dict
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

    def play(self) -> None:
        self.mpris_player.Play()

    def play_pause(self) -> None:
        self.mpris_player.PlayPause()

    def pause(self) -> None:
        self.mpris_player.Pause()

    def stop(self) -> None:
        self.mpris_player.Stop()

    def seek(self, offset: int) -> None:
        self.mpris_player.Seek(offset)

    def set_position(self, to_position: int) -> None:
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

    def get(self, interface_name: str, property_name: str) -> Any:
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
        return self.get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")

    @property
    def position(self) -> int:
        return self.get("org.mpris.MediaPlayer2.Player", "Position")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.get("org.mpris.MediaPlayer2.Player", "Metadata")

    @property
    def trackid(self) -> str:
        return self.metadata["mpris:trackid"]

    @cached_property
    def can_control(self) -> bool:
        return self.get("org.mpris.MediaPlayer2.Player", "CanControl")

    @cached_property
    def can_seek(self) -> bool:
        return self.get("org.mpris.MediaPlayer2.Player", "CanSeek")

    @cached_property
    def can_pause(self) -> bool:
        return self.get("org.mpris.MediaPlayer2.Player", "CanPause")

    @cached_property
    def can_play(self) -> bool:
        return self.get("org.mpris.MediaPlayer2.Player", "CanPlay")


class NoValidMprisPlayers(Exception):
    pass
