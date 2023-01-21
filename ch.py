"""Creates a console or gui based menu of chapters, from a default file named ch.json in
the current directory. A chapters file may also be specified with the -f
option. On startup, the application displays a list of running MPRIS enabled
players to connect to. If only one player is running then it directly connects
to the running player.
"""

import argparse
import logging

import lib.helpers as mpris_helpers
from lib.dbus_mpris.core import NoValidMprisPlayersError, PlayerFactory
from lib.ui.console_ui import build_console_menu
from lib.ui.gui import build_gui_menu

# logging.basicConfig(filename="log.txt", filemode="w", level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def main():
    arguments = get_arguments()
    player_instance_name = arguments.p
    # Retrieve list of running mpris enabled players
    running_players = PlayerFactory.get_running_player_names()
    if len(running_players) == 0:
        print("No mpris enabled players are running.")
        return

    try:
        logger.info("Creating player")
        if player_instance_name:
            logger.info(f"Player name specified via -p is {player_instance_name}")
            selected_player = mpris_helpers.get_player(
                player_instance_name, running_players
            )
        else:
            selected_player = mpris_helpers.get_selected_player(running_players)
        logger.info("Created player")
        chapters_file = arguments.f
        if arguments.g:
            launch_gui(arguments, chapters_file, selected_player)
        else:
            launch_console(arguments, chapters_file, selected_player)

    except NoValidMprisPlayersError as err:
        print(err)
    except FileNotFoundError as fe:
        print(
            "Chapters file not found. Use -h option to learn how to provide a chapters file."
        )
    #    except Exception as err:
    #        logger.error(err)
    return


def launch_gui(arguments, chapters_file, player):
    gui_window = build_gui_menu(chapters_file, player)
    gui_window.show_display()


def launch_console(arguments, chapters_file, selected_player):
    chapters_console_menu = build_console_menu(
        chapters_file=chapters_file,
        player=selected_player,
        reload_option=arguments.r,
        player_controls_option=arguments.c,
    )
    chapters_console_menu.display_menu()
    if chapters_console_menu.reload_chapters_on_exit:
        launch_console(arguments, chapters_file, selected_player)


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Creates a console based menu of chapters,"
            " from a default file named ch.json in the current directory. "
            "A chapters file may also be specified with the -f option. "
            "On startup, the application displays a list of running MPRIS enabled players to connect to. "
            "If only one player is running then it directly connects to the running player."
        )
    )
    parser.add_argument(
        "-f",
        action="store",
        required=False,
        default="ch.json",
        help="The file name of the file containing the "
        "chapter titles and their time offsets in a JSON document: "
        '{"title":"title name", "chapters":{"first chapter name" : "hh:mm:ss","second chapter name" : "hh:mm:ss"}}',
    )
    parser.add_argument(
        "-p",
        action="store",
        required=False,
        help="The name of the player instance to connect to.",
    )
    parser.add_argument(
        "-r",
        action="store_true",
        required=False,
        default=False,
        help="Include a option to reload the chapters file. Only for console mode.",
    )
    parser.add_argument(
        "-c",
        action="store_true",
        required=False,
        default=False,
        help="Include a option to control the player via a sub-menu. Only for console mode.",
    )
    parser.add_argument(
        "-g",
        action="store_true",
        required=False,
        default=False,
        help="Launch graphical user interface.",
    )
    arguments = parser.parse_args()
    return arguments


if __name__ == "__main__":
    main()
