import dbus
from consolemenu import SelectionMenu


def get_running_player_instance_names() -> dict:
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


def select_player(player_names: list) -> str:
    """Presents the user with an interactive console to select a player
    instance.

    Arguments:
    player_names is a list containing the names of the player instances.

    Returns a string containing the player name selected by the user"""

    if not isinstance(player_names, list):
        raise TypeError("player_names is not a list")

    selection = SelectionMenu.get_selection(
        title="Select a player to connect to:",
        strings=player_names,
        show_exit_option=False,
    )
    return player_names[selection]


if __name__ == "__main__":
    player_instance_names = get_running_player_instance_names()
    print(select_player(list(player_instance_names.keys())))
