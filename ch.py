"""Creates a console based menu of chapters, from a default file named ch.json in
the current directory. A chapters file may also be specified with the -f
option. On startup, the application displays a list of running MPRIS enabled 
players to connect to. If only one player is running then it directly connects
to the running player.
"""

import argparse
import logging

import lib.dbus_mpris.helpers as mpris_helpers
from lib.dbus_mpris.core import NoValidMprisPlayersError, Player, PlayerFactory
from lib.ui.ui import ChaptersMenuConsole, ChaptersMenuConsoleBuilder

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
        chapters_console_menu = build_console_menu(
            chapters_file=chapters_file,
            player=selected_player,
            reload_option=arguments.r,
            player_controls_option=arguments.c,
        )
        while True:
            chapters_console_menu.display_menu()
            if chapters_console_menu.reload_chapters_on_exit:
                chapters_console_menu = build_console_menu(
                    chapters_file=chapters_file,
                    player=selected_player,
                    reload_option=arguments.r,
                    player_controls_option=arguments.c,
                )
            else:
                break

    except NoValidMprisPlayersError as err:
        print(err)
    except FileNotFoundError as fe:
        print(
            "Chapters file not found. Use -h option to learn how to provide a chapters file."
        )
    except Exception as err:
        logger.error(err)
    return


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
        help="Include a option to reload the chapters file.",
    )
    parser.add_argument(
        "-c",
        action="store_true",
        required=False,
        default=False,
        help="Include a option to control the player via a sub-menu",
    )
    arguments = parser.parse_args()
    return arguments


def build_console_menu(
        chapters_file: str,
        player: Player,
        reload_option: bool,
        player_controls_option: bool,
) -> ChaptersMenuConsole:
    """Orchestrates the building of the console menu by using the capabilities of the ChaptersMenuConsoleBuilder.
    This is the Director in the Builder Pattern"""

    console_builder = ChaptersMenuConsoleBuilder(chapters_file, player)
    if reload_option:
        console_builder.build_reload_chapters_item()
    if player_controls_option:
        console_builder.build_player_control_menu()
    console_builder.build_chapters_menu()
    return console_builder.chapters_menu_console


if __name__ == "__main__":
    main()
