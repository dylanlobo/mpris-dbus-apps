"""Creates a console or gui based menu of chapters, from a default file named ch.ch in
the current directory. A chapters file may also be specified with the -f
option. On startup, the application displays a list of running MPRIS enabled
players to connect to. If only one player is running then it directly connects
to the running player.
"""

import argparse
import logging

import lib.helpers as mpris_helpers
from lib.dbus_mpris.player import (
    PlayerCreationError,
    NoValidMprisPlayersError,
    PlayerFactory,
)
from lib.ui.console_ui import build_console_menu
from lib.ui.gui import build_gui_menu

# logging.basicConfig(filename="log.txt", filemode="w", level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    arguments = get_arguments()
    running_players = PlayerFactory.get_running_player_names()
    selected_player = None
    chapters_file = arguments.f
    try:
        if len(running_players) == 1:
            player_names = list(running_players.keys())
            selected_player_name = player_names[0]
            selected_player_fq_name = running_players[selected_player_name]
            logger.debug("Creating player")
            selected_player = PlayerFactory.get_player(
                selected_player_fq_name, selected_player_name
            )

            logger.debug("Created player")
    except PlayerCreationError as e:
        print(e)
    if not arguments.c:
        launch_gui(chapters_file, selected_player)
        return
    try:
        if len(running_players) == 0:
            print("No mpris enabled players are running.")
            return
        if not selected_player:
            logger.debug("Creating player")
            selected_player = mpris_helpers.get_selected_player(running_players)
            logger.debug("Created player")
        chapters_file = arguments.f
        if not chapters_file:
            raise FileNotFoundError()
        launch_console(arguments, chapters_file, selected_player)

    except (NoValidMprisPlayersError, PlayerCreationError) as err:
        print(err)
    except FileNotFoundError:
        print(
            "Chapters file not found. Use -h option to learn how to provide a chapters"
            " file."
        )
    #    except Exception as err:
    #        logger.error(err)
    return


def launch_gui(chapters_file=None, player=None):
    gui_window = build_gui_menu(chapters_file, player)
    gui_window.show_display()


def launch_console(arguments, chapters_file, selected_player):
    chapters_console_menu = build_console_menu(
        chapters_file=chapters_file,
        player=selected_player,
        reload_option=arguments.r,
        player_controls_option=arguments.p,
    )
    chapters_console_menu.display_menu()
    if chapters_console_menu.reload_chapters_on_exit:
        launch_console(arguments, chapters_file, selected_player)


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Chapters is media player controller that provides "chapter" '
            "functionality to any media (audio/video) that is playing on a "
            "MPRIS enabled media player."
            "Chapters utilises chapter infomation stored in a simple JSON format file."
            "The JSON chapters file can be specified at launch via the -f option. "
            "In gui mode (default mode), the application presents the user with "
            "a simple GUI interface. "
            "In console mode, on startup, the application displays a list of "
            "running MPRIS enabled players to connect to. "
            "If only one player is running then it directly connects to the running "
            "player."
        )
    )
    parser.add_argument(
        "-f",
        action="store",
        nargs="?",
        required=False,
        default=None,
        help="The file name (.ch extension) of the file containing the "
        "chapter titles and their time offsets in a JSON document: "
        '{"title":"title name", "chapters":{"first chapter name" : "hh:mm:ss"'
        ',"second chapter name" : "hh:mm:ss"}}',
    )
    parser.add_argument(
        "-r",
        action="store_true",
        required=False,
        default=False,
        help="Include a option to reload the chapters file. Only for console mode.",
    )
    parser.add_argument(
        "-p",
        action="store_true",
        required=False,
        default=False,
        help="Include a option to control the player via a sub-menu."
        "Only for console mode.",
    )
    parser.add_argument(
        "-c",
        action="store_true",
        required=False,
        default=False,
        help="Launch in console mode (terminal interface).",
    )
    arguments = parser.parse_args()
    return arguments


if __name__ == "__main__":
    main()
