"""Convenience wrappers for DBbus MPRIS core functionality"""
from abc import ABC, abstractmethod
import re
import logging
from typing import Any, Dict
from functools import lru_cache, cached_property, wraps

try:
    import pydbus
except ImportError:
    import dbus

logger = logging.getLogger(__name__)


@lru_cache()
def is_object_path_valid(path: str) -> bool:
    """Whether this is a valid object path.
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
        self.connect()

    def connect(self):
        pass

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
    def next(self) -> None:
        ...

    @abstractmethod
    def previous(self) -> None:
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


def reconnect_player(func):
    @wraps(func)
    def decorator(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            logger.error(type(e))
            logger.info(e)
            logger.info("Possible player discconnection, attempting to reconnect")
            self.connect()
            logger.info(f"Attempting to call {func.__name__} again")
            func(self, *args, **kwargs)

    return decorator


def handle_player_error(func: callable):
    def decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error("An error occured when attempting to call the player")
            logger.error(type(e))
            raise

    return decorator


class PlayerProxy(Player):
    def __init__(self, player: Player):
        self._player = player

    def set_player(self, player: Player):
        self._player = player

    @handle_player_error
    def connect(self):
        if self._player:
            self._player.connect()

    @reconnect_player
    def raise_window(self) -> None:
        if self._player:
            self._player.raise_window()

    @reconnect_player
    def play(self) -> None:
        if self._player:
            self._player.play()

    @reconnect_player
    @handle_player_error
    def play_pause(self) -> None:
        if self._player:
            self._player.play_pause()

    @reconnect_player
    def pause(self) -> None:
        if self._player:
            self._player.pause()

    @reconnect_player
    def next(self) -> None:
        if self._player:
            self._player.next()

    @reconnect_player
    def previous(self) -> None:
        if self._player:
            self._player.previous()

    @reconnect_player
    def stop(self) -> None:
        if self._player:
            self._player.stop()

    @reconnect_player
    def seek(self, offset: int) -> None:
        if self._player:
            self._player.seek(offset)

    @reconnect_player
    def set_position(self, to_position: int) -> None:
        if self._player:
            self._player.set_position(to_position)

    @reconnect_player
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

    def connect(self):
        bus = dbus.SessionBus()
        try:
            self._proxy = bus.get_object(self._name, "/org/mpris/MediaPlayer2")
        except Exception as e:
            logger.error(f"Caught exceptio {type(e)}")
            logger.error(f"Unable to retrieve the {self._name} proxy from dbus.")
            logger.error(e)
            raise Exception(
                f"Unable to connect to {self._ext_name},"
                f" check if {self._ext_name} it is running."
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

    def next(self) -> None:
        self.mpris_player.Next()

    def previous(self) -> None:
        self.mpris_player.Previous()

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
                "Unable to use SetPosition(trackid,postion),"
                " due to invalid trackid value."
            )
            logger.debug("Attempting to use Seek() to set the requested postion.")
            cur_pos = self.position
            seek_to_position = to_position - cur_pos
            self.seek(seek_to_position)

    def get(
        self, property_name: str, interface_name: str = "org.mpris.MediaPlayer2.Player"
    ) -> Any:
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
        return self.get(property_name="PlaybackStatus")

    @property
    def position(self) -> int:
        return self.get(property_name="Position")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.get(property_name="Metadata")

    @property
    def trackid(self) -> str:
        if "mpris:trackid" in self.metadata:
            return self.metadata["mpris:trackid"]
        else:
            logger.warning(
                f"Metadata from {self.ext_name} does not contain mpris:trackid\n"
                f"Returning an empty string instead"
            )
            return ""

    @cached_property
    def can_control(self) -> bool:
        return self.get(property_name="CanControl")

    @cached_property
    def can_seek(self) -> bool:
        return self.get(property_name="CanSeek")

    @cached_property
    def can_pause(self) -> bool:
        return self.get(property_name="CanPause")

    @cached_property
    def can_play(self) -> bool:
        return self.get(property_name="CanPlay")


class Player_pydbus(Player):
    """A convenience class whose object instances encapsulates
    an MPRIS player object and exposes a subset of
    the org.mpris.MediaPlayer2.Player interface."""

    def __init__(self, mpris_player_name, ext_player_name) -> None:
        super().__init__(mpris_player_name, ext_player_name)

    def connect(self):
        bus = pydbus.SessionBus()
        try:
            self._proxy = bus.get(self._name, "/org/mpris/MediaPlayer2")
        except KeyError as e:
            logger.error(e)
            logger.error(f"Unable to retrieve the {self._name} proxy from dbus.")
            raise PlayerConnectionError(
                f"Unable to connect to {self._ext_name},"
                f" check if {self._ext_name} it is running."
            )

    def get(
        self, property_name: str, interface_name="org.mpris.MediaPlayer2.Player"
    ) -> Any:
        return self.mpris_player_properties.Get(interface_name, property_name)

    def raise_window(self) -> None:
        self.mpris_media_player2.Raise()

    def play(self) -> None:
        self.mpris_player.Play()

    def play_pause(self) -> None:
        self.mpris_player.PlayPause()

    def pause(self) -> None:
        self.mpris_player.Pause()

    def next(self) -> None:
        self.mpris_player.Next()

    def previous(self) -> None:
        self.mpris_player.Previous()

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
                "Unable to use SetPosition(trackid,postion),"
                " due to invalid trackid value."
            )
            logger.debug("Attempting to use Seek() to set the requested postion.")
            cur_pos = self.position
            seek_to_position = to_position - cur_pos
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
        return self.get(property_name="PlaybackStatus")

    @property
    def position(self) -> int:
        return self.get(property_name="Position")

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.get(property_name="Metadata")

    @property
    def trackid(self) -> str:
        if "mpris:trackid" in self.metadata:
            return self.metadata["mpris:trackid"]
        else:
            logger.warning(
                f"Metadata from {self.ext_name} does not contain mpris:trackid\n"
                f"Returning an empty string instead"
            )
            return ""

    @cached_property
    def can_control(self) -> bool:
        return self.get(property_name="CanControl")

    @cached_property
    def can_seek(self) -> bool:
        return self.get(property_name="CanSeek")

    @cached_property
    def can_pause(self) -> bool:
        return self.get(property_name="CanPause")

    @cached_property
    def can_play(self) -> bool:
        return self.get(property_name="CanPlay")


class PlayerFactory:
    unuseable_player_names = []

    @staticmethod
    def get_running_player_names() -> Dict[str, str]:
        """Retrieves media player instances names of currently running
        MPRIS D-Bus enabled players, from the dbus SessionBus.
        returns: a dictionary. The dictionary key is the unqualified
        player instance name and value is the fully qualified player name."""

        running_player_names = {}
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
                if service in PlayerFactory.unuseable_player_names:
                    continue
                service_suffix = service[media_player_prefix_len + 1 :]
                try:
                    # Not all org.mpris.MediaPlayer2 instances are useable
                    # Attempting (relatively cheap) player creation to
                    # exclude unusable players
                    PlayerFactory.get_player(str(service), service_suffix)
                    running_player_names[service_suffix] = str(service)
                except PlayerCreationError:
                    PlayerFactory.unuseable_player_names.append(str(service))
        return running_player_names

    @staticmethod
    def get_player(fq_player_name, short_player_name) -> Player:
        try:
            type(pydbus)
            logger.debug("Creating a Player_pydbus instance.")
            player = Player_pydbus(fq_player_name, short_player_name)
            return PlayerProxy(player)
        except (NameError, KeyError):
            logger.debug("Creating a Player_dbus_python instance.")
            player = Player_dbus_python(fq_player_name, short_player_name)
            return PlayerProxy(player)
        except PlayerConnectionError as per:
            raise PlayerCreationError(per)
        except Exception as e:
            logger.error(type(e))
            logger.error(e)
            raise PlayerCreationError(e)


class NoValidMprisPlayersError(Exception):
    pass


class PlayerConnectionError(Exception):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        logger.error("Player connection failed")


class PlayerCreationError(Exception):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        logger.error("Player creation failed")
