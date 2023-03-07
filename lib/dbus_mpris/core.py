"""Convenience wrappers for DBbus MPRIS core functionality"""
from abc import ABC, abstractmethod
import re
import logging
from typing import Any, Dict
from functools import lru_cache, cached_property

try:
    import dbus
    from dbus import DBusException
except ImportError:
    import pydbus

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


class Player(ABC):
    """A convenience class whose object instances encapsulates
    an MPRIS player object and exposes a subset of
    the org.mpris.MediaPlayer2.Player interface."""

    @abstractmethod
    def __init__(self, mpris_player_name, ext_player_name) -> None:
        self._name = mpris_player_name
        self._ext_name = ext_player_name

    @abstractmethod
    def raise_window(self) -> None:
        ...

    @abstractmethod
    def play(self) -> None:
        ...

    @abstractmethod
    def play_pause(self) -> None:
        ...

    @abstractmethod
    def pause(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    @abstractmethod
    def seek(self, offset: int) -> None:
        ...

    @abstractmethod
    def set_position(self, to_position: int) -> None:
        ...

    def get(self, interface_name: str, property_name: str) -> Any:
        ...

    @property
    @abstractmethod
    def mpris_player(self) -> Any:
        ...

    @property
    @abstractmethod
    def mpris_media_player2(self) -> Any:
        ...

    @property
    @abstractmethod
    def mpris_player_properties(self) -> Any:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
        return self._name

    @property
    @abstractmethod
    def ext_name(self) -> str:
        ...
        return self._ext_name

    @property
    @abstractmethod
    def playback_status(self) -> str:
        ...

    @property
    @abstractmethod
    def position(self) -> int:
        ...

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        ...

    @property
    @abstractmethod
    def trackid(self) -> str:
        ...

    @cached_property
    @abstractmethod
    def can_control(self) -> bool:
        ...

    @cached_property
    @abstractmethod
    def can_seek(self) -> bool:
        ...

    @cached_property
    @abstractmethod
    def can_pause(self) -> bool:
        ...

    @cached_property
    @abstractmethod
    def can_play(self) -> bool:
        ...


class PlayerProxy(Player):
    def __init__(self, player: Player):
        self._player = player

    def set_player(self, player: Player):
        self._player = player

    def raise_window(self) -> None:
        if self._player:
            self._player.raise_window()

    def play(self) -> None:
        if self._player:
            self._player.play()

    def play_pause(self) -> None:
        if self._player:
            self._player.play_pause()

    def pause(self) -> None:
        if self._player:
            self._player.pause()

    def stop(self) -> None:
        if self._player:
            self._player.stop()

    def seek(self, offset: int) -> None:
        if self._player:
            self._player.seek(offset)

    def set_position(self, to_position: int) -> None:
        if self._player:
            self._player.set_position(to_position)

    def get(self, interface_name: str, property_name: str) -> Any:
        if self._player:
            self._player.get(interface_name, property_name)

    @property
    def mpris_player(self) -> Any:
        if self._player:
            return self._player.mpris_player
        else:
            return None

    @property
    def mpris_media_player2(self) -> Any:
        if self._player:
            return self._player.mpris_media_player2
        else:
            return None

    @property
    def mpris_player_properties(self) -> Any:
        if self._player:
            return self._player.mpris_player_properties
        else:
            return None

    @property
    def name(self) -> str:
        if self._player:
            return self._player.name
        else:
            return None

    @property
    def ext_name(self) -> str:
        if self._player:
            return self._player.ext_name
        else:
            return None

    @property
    def playback_status(self) -> str:
        if self._player:
            return self._player.playback_status
        else:
            return None

    @property
    def position(self) -> int:
        if self._player:
            return self._player.position
        else:
            return None

    @property
    def metadata(self) -> Dict[str, Any]:
        if self._player:
            return self._player.metadata
        else:
            return None

    @property
    def trackid(self) -> str:
        if self._player:
            return self._player.trackid
        else:
            return None

    @cached_property
    def can_control(self) -> bool:
        if self._player:
            return self._player.can_control
        else:
            return None

    @cached_property
    def can_seek(self) -> bool:
        if self._player:
            return self._player.can_seek
        else:
            return None

    @cached_property
    def can_pause(self) -> bool:
        if self._player:
            return self._player.can_pause
        else:
            return None

    @cached_property
    def can_play(self) -> bool:
        if self._player:
            return self._player.can_play
        else:
            return None


class Player_dbus_python(Player):
    """A convenience class whose object instances encapsulates
    an MPRIS player object and exposes a subset of
    the org.mpris.MediaPlayer2.Player interface."""

    def __init__(self, mpris_player_name, ext_player_name) -> None:
        super().__init__(mpris_player_name, ext_player_name)
        bus = dbus.SessionBus()
        try:
            self._proxy = bus.get_object(self._name, "/org/mpris/MediaPlayer2")
        except DBusException as e:
            logger.error(f"Unable to retrieve the {self._name} proxy from dbus.")
            logger.error(e)
            raise Exception(
                f"Unable to connect to {self._ext_name}, check if {self._ext_name} it is running."
            )
        self._media_player2 = dbus.Interface(
            self._proxy, dbus_interface="org.mpris.MediaPlayer2"
        )
        self._player = dbus.Interface(
            self._proxy, dbus_interface="org.mpris.MediaPlayer2.Player"
        )
        self._player_properties = dbus.Interface(
            self._player, dbus_interface="org.freedesktop.DBus.Properties"
        )

    def raise_window(self) -> None:
        self.mpris_media_player2.Raise()

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
        if is_object_path_valid(self.trackid):
            self.mpris_player.SetPosition(self.trackid, to_position)
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
            self.seek(seek_to_position)

    def get(self, interface_name: str, property_name: str) -> Any:
        return self.mpris_player_properties.Get(interface_name, property_name)

    @property
    def mpris_player(self):
        return self._player

    @property
    def mpris_media_player2(self):
        return self._media_player2

    @property
    def mpris_player_properties(self):
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


class Player_pydbus(Player):
    """A convenience class whose object instances encapsulates
    an MPRIS player object and exposes a subset of
    the org.mpris.MediaPlayer2.Player interface."""

    def __init__(self, mpris_player_name, ext_player_name) -> None:
        super().__init__(mpris_player_name, ext_player_name)
        bus = pydbus.SessionBus()
        try:
            self._proxy = bus.get(self._name, "/org/mpris/MediaPlayer2")
        except Exception as e:
            logger.error(f"Unable to retrieve the {self._name} proxy from dbus.")
            logger.error(type(e))
            raise Exception(
                f"Unable to connect to {self._ext_name}, check if {self._ext_name} it is running."
            )

    def raise_window(self) -> None:
        self.mpris_media_player2.Raise()

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
        if is_object_path_valid(self.trackid):
            self.mpris_player.SetPosition(self.trackid, to_position)
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
            self.seek(seek_to_position)

    @property
    def mpris_player(self):
        return self._proxy

    @property
    def mpris_media_player2(self):
        return self._proxy

    @property
    def mpris_player_properties(self):
        return self._proxy

    @property
    def name(self) -> str:
        return self._name

    @property
    def ext_name(self) -> str:
        return self._ext_name

    @property
    def playback_status(self) -> str:
        return self.mpris_player_properties.PlaybackStatus

    @property
    def position(self) -> int:
        return self.mpris_player_properties.Position

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.mpris_player_properties.Metadata

    @property
    def trackid(self) -> str:
        return self.mpris_player_properties.Metadata["mpris:trackid"]

    @cached_property
    def can_control(self) -> bool:
        return self.mpris_player_properties.CanControl

    @cached_property
    def can_seek(self) -> bool:
        return self.mpris_player_properties.CanSeek

    @cached_property
    def can_pause(self) -> bool:
        return self.mpris_player_properties.CanPause

    @cached_property
    def can_play(self) -> bool:
        return self.mpris_player_properties.CanPlay


class PlayerFactory:
    @staticmethod
    def get_running_player_names() -> Dict[str, str]:
        """Retrieves media player instances names of currently running
        MPRIS D-Bus enabled players, from the dbus SessionBus.
        returns: a dictionary. The dictionary key is the unqualified
        player instance name and value is the fully qualified player name."""

        running_players = {}
        media_player_prefix = "org.mpris.MediaPlayer2"
        media_player_prefix_len = len(media_player_prefix)
        try:
            all_service_names = dbus.SessionBus().list_names()
            logger.info("Retrieved running services with dbus-python")
        except NameError:
            bus = pydbus.SessionBus()
            remote_object = bus.get(
                "org.freedesktop.DBus",  # Bus name
                "/org/freedesktop/DBus",  # Object path
            )
            all_service_names = remote_object.ListNames()

        for service in all_service_names:
            if media_player_prefix in service:
                service_suffix = service[media_player_prefix_len + 1 :]
                running_players[service_suffix] = str(service)
        return running_players

    @staticmethod
    def get_player(fq_player_name, short_player_name) -> Player:
        try:
            type(dbus)
            logger.info("Creating a Player_dbus_python instance.")
            player = Player_dbus_python(fq_player_name, short_player_name)
            return PlayerProxy(player)
        except NameError:
            logger.info("Creating a Player_pydbus instance.")
            player = Player_pydbus(fq_player_name, short_player_name)
            return PlayerProxy(player)


class NoValidMprisPlayersError(Exception):
    pass
