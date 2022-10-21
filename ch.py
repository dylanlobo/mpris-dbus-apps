"""Creates a console based menu of chapters, from a default file named ch.json in
the current directory. A chapters file may also be specified with the -f
option. On startup, the application displays a list of running MPRIS enabled 
players to connect to. If only one player is running then it directly connects
to the running player.
"""

import argparse
import json
import logging
import os
from json.decoder import JSONDecodeError
from typing import Dict, Tuple

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem
from consolemenu.items import SubmenuItem

import dbus_mpris.helpers as mpris_helpers
from dbus_mpris.core import NoValidMprisPlayersError, Player

# logging.basicConfig(filename="log.txt", filemode="w", level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    arguments = get_arguments()
    # Retrieve list of running mpris enabled players
    running_players = Player.get_running_player_names()
    if len(running_players) == 0:
        print("No mpris enabled players are running.")
        return

    try:
        logger.info("Creating player")
        player = mpris_helpers.get_selected_player(running_players)
        logger.info("Created player")
        chapters_file = arguments.f
        chapters_console_menu = build_console_menu(chapters_file, player)
        while True:
            chapters_console_menu.display_menu()
            if chapters_console_menu.reload_chapters_on_exit:
                chapters_console_menu = build_console_menu(chapters_file, player)
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
    arguments = parser.parse_args()
    return arguments


class ChaptersMenuConsole:
    def __init__(self, title: str) -> None:
        self._reload_chapters = False
        self._title = title
        self._console_main_menu = ConsoleMenu(title=self._title, subtitle="Chapters")

    @property
    def console_main_menu(self) -> ConsoleMenu:
        return self._console_main_menu

    @property
    def reload_chapters_on_exit(self) -> bool:
        return self._reload_chapters

    def display_menu(self):
        self.console_main_menu.show()

    def set_reload_chapters_on_exit(self) -> None:
        self._reload_chapters = True


class ChaptersMenuConsoleBuilder:
    def __init__(self, chapters_filename: str, player: Player) -> None:
        try:
            self._chapters_title, self._chapters = self._load_chapters_file(
                chapters_filename
            )
        except FileNotFoundError as fe:
            logger.error(fe)
            raise fe

        self._chapters_menu_console = ChaptersMenuConsole(title=self._chapters_title)
        self._player = player

    @staticmethod
    def _load_chapters_file(chapters_file: str) -> Tuple[str, Dict[str, str]]:
        if os.path.isfile(chapters_file) is False:
            logger.error(f"{chapters_file} does not exist")
            raise FileNotFoundError(f"{chapters_file} does not exist")
        chapters = {}
        title = "No Title"
        try:
            with open(chapters_file, "r") as f:
                json_dict = json.load(f)
        except JSONDecodeError as e:
            logger.critical(
                f"The file {chapters_file} is not a valid JSON document. {e}"
            )
            raise ValueError(f"The file {chapters_file} is not a valid JSON document.")

        if json_dict["title"]:
            title = json_dict["title"]
        if json_dict["chapters"]:
            chapters = json_dict["chapters"]
        else:
            raise ValueError(f'{chapters_file} file is missing "chapters" object')
        return title, chapters

    @property
    def chapters_menu_console(self) -> ChaptersMenuConsole:
        return self._chapters_menu_console

    def build_default_setup(self) -> None:
        self.build_reload_chapters_item()
        self.build_player_control_menu()
        self.build_chapters_menu()

    def build_reload_chapters_item(self) -> None:
        self.chapters_menu_console.console_main_menu.append_item(
            FunctionItem(
                "Reload Chapters",
                self.chapters_menu_console.set_reload_chapters_on_exit,
                should_exit=True,
            )
        )

    def build_chapters_menu(self):
        for chapter_name, time_offset in self._chapters.items():
            self.chapters_menu_console.console_main_menu.append_item(
                FunctionItem(
                    f"{chapter_name} ({time_offset})",
                    self._player.set_position,
                    [mpris_helpers.to_microsecs(time_offset)],
                )
            )

    def build_player_control_menu(self):
        command_menu = ConsoleMenu(title="Player Control Commands")
        command_submenu_item = SubmenuItem(
            text="Player Control Commands",
            menu=self.chapters_menu_console.console_main_menu,
            submenu=command_menu,
        )
        command_menu.append_item(
            FunctionItem(
                "Play/Pause",
                self._player.play_pause,
            )
        )
        command_menu.append_item(
            FunctionItem(
                "Skip Forward 30 sec",
                self._player.seek,
                [mpris_helpers.to_microsecs("00:00:30")],
            )
        )
        command_menu.append_item(
            FunctionItem(
                "Skip Back 30 sec",
                self._player.seek,
                [mpris_helpers.to_microsecs("00:00:30") * -1],
            )
        )
        command_menu.append_item(
            FunctionItem(
                "Skip Forward 1 min",
                self._player.seek,
                [mpris_helpers.to_microsecs("00:01:00")],
            )
        )
        command_menu.append_item(
            FunctionItem(
                "Skip Back 1 min",
                self._player.seek,
                [mpris_helpers.to_microsecs("00:01:00") * -1],
            )
        )
        self.chapters_menu_console.console_main_menu.append_item(command_submenu_item)


def build_console_menu(chapters_file: str, player: Player) -> ChaptersMenuConsole:
    console_builder = ChaptersMenuConsoleBuilder(chapters_file, player)
    console_builder.build_default_setup()
    return console_builder.chapters_menu_console


if __name__ == "__main__":
    main()
