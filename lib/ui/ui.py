import json
import logging
import os

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem
from consolemenu.items import SubmenuItem
from json import JSONDecodeError
from typing import Any, Tuple, Dict
from ..dbus_mpris.core import Player
from .. import helpers as mpris_helpers

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class ChaptersMenuConsole:
    def __init__(self, title: str) -> None:
        self._reload_chapters = False
        self._title = title
        self._console_main_menu = ConsoleMenu(title=self._title, subtitle="Chapters")

    @property
    def reload_chapters_on_exit(self) -> bool:
        return self._reload_chapters

    def append_main_menu_item(self, menu_item: Any):
        self._console_main_menu.append_item(menu_item)

    def display_menu(self):
        self._console_main_menu.show()

    def set_reload_chapters_on_exit(self) -> None:
        self._reload_chapters = True


class ChaptersMenuConsoleBuilder:
    def __init__(self, chapters_filename: str, player: Player) -> None:
        try:
            self._chapters_title, self._chapters = mpris_helpers.load_chapters_file(
                chapters_filename
            )
        except FileNotFoundError as fe:
            logger.error(fe)
            raise fe

        self._chapters_menu_console = ChaptersMenuConsole(title=self._chapters_title)
        self._player = player

    @property
    def chapters_menu_console(self) -> ChaptersMenuConsole:
        return self._chapters_menu_console

    def build_complete_setup(self) -> None:
        self.build_reload_chapters_item()
        self.build_player_control_menu()
        self.build_chapters_menu()

    def build_reload_chapters_item(self) -> None:
        self.chapters_menu_console.append_main_menu_item(
            FunctionItem(
                "Reload Chapters",
                self.chapters_menu_console.set_reload_chapters_on_exit,
                should_exit=True,
            )
        )

    def build_chapters_menu(self):
        for chapter_name, time_offset in self._chapters.items():
            self.chapters_menu_console.append_main_menu_item(
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
                "Skip Forward 10 sec",
                self._player.seek,
                [mpris_helpers.to_microsecs("00:00:10")],
            )
        )
        command_menu.append_item(
            FunctionItem(
                "Skip Back 10 sec",
                self._player.seek,
                [mpris_helpers.to_microsecs("00:00:10") * -1],
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
        self.chapters_menu_console.append_main_menu_item(command_submenu_item)
