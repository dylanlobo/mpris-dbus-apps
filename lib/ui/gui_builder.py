from enum import IntEnum
from functools import partial
from typing import Tuple, List, Dict, Protocol
from pathlib import Path
from lib.ui.gui_controller import GuiController
import lib.helpers as helpers
import lib.ui.gui_classic as gui_classic
from lib.dbus_mpris.player import (
    Player,
    PlayerProxy,
    PlayerFactory,
    PlayerCreationError,
)
import logging

logger = logging.getLogger(__name__)


class AppMainWindow(Protocol):
    """The main window protocol class for the application."""

    def show_display(self):
        ...


class GuiMode(IntEnum):
    CLASSIC = 1
    THEMED = 2


class AppGuiBuilder:
    def __init__(
        self,
        chapters_filename: str,
        player: PlayerProxy,
        mode: GuiMode = GuiMode.THEMED,
    ):
        self._chapters_filename = chapters_filename
        self._view: AppMainWindow = None
        if mode == GuiMode.THEMED:
            import lib.ui.gui_themed as gui_themed

            self._view = gui_themed.AppMainWindowThemed()
        else:
            self._view = gui_classic.AppMainWindowClassic()
        if not player:
            self._player = PlayerProxy(None)
        else:
            self._player = player
        self._gui_controller = GuiController(self._view, self._player, self)
        self._gui_controller.set_chapters_filename(chapters_filename)

    def create_menu_bar_bindings(self):
        self._view.menu_bar.bind_connect_to_player_command(
            self._gui_controller.handle_connection_command
        )
        self._view.menu_bar.bind_load_chapters_file_command(
            self._gui_controller.handle_load_chapters_file_command
        )
        self._view.menu_bar.bind_load_chapters_from_youtube_command(
            self._gui_controller.handle_load_chapters_from_youtube
        )

        self._view.menu_bar.bind_save_chapters_file_command(
            self._gui_controller.handle_save_chapters_file_command
        )

    def create_chapters_panel_bindings(
        self, chapters_title: str = "", chapters: Dict[str, str] = {}
    ):
        (
            listbox_items,
            chapters_position_functions,
        ) = self._build_chapters_listbox_bindings(chapters)
        self._create_listbox_items(
            chapters_title, listbox_items, chapters_position_functions
        )

    def _build_chapters_listbox_bindings(
        self, chapters: Dict[str, str]
    ) -> Tuple[List[str], List[callable]]:
        listbox_items: List[str] = []
        chapters_position_functions: List[callable] = []
        chapter: str
        position: str
        if chapters:
            n_items = len(chapters)
            for i, (chapter, position) in enumerate(chapters.items()):
                if n_items >= 10:
                    index = f"0{i+1}" if i < 9 else f"{i+1}"
                else:
                    index = f"{i+1}"
                listbox_items.append(f"{index}.  {chapter} ({position})")
                chapters_position_functions.append(
                    partial(self._gui_controller.set_player_position, position)
                )
        return (listbox_items, chapters_position_functions)

    def _create_listbox_items(
        self,
        chapters_title: str,
        listbox_items: List[str],
        chapters_position_functions: List[callable],
    ):
        self._view.set_main_window_title(chapters_title)
        self._view.set_chapters(chapters=listbox_items)
        self._view.bind_chapters_selection_commands(
            chapters_selection_action_functs=chapters_position_functions
        )

    def create_player_control_panel_bindings(self):
        button_action_funcs = {
            "Play/Pause": self._gui_controller.play_pause_player,
            ">|": self._gui_controller.next_player,
            ">": partial(self._gui_controller.skip_player, offset="00:00:05"),
            ">>": partial(self._gui_controller.skip_player, offset="00:00:10"),
            ">>>": partial(self._gui_controller.skip_player, offset="00:01:00"),
            "<": partial(
                self._gui_controller.skip_player,
                offset="00:00:05",
                direction=helpers.Direction.REVERSE,
            ),
            "<<": partial(
                self._gui_controller.skip_player,
                offset="00:00:10",
                direction=helpers.Direction.REVERSE,
            ),
            "<<<": partial(
                self._gui_controller.skip_player,
                offset="00:01:00",
                direction=helpers.Direction.REVERSE,
            ),
            "|<": self._gui_controller.previous_player,
        }
        self._view.bind_player_controls_commands(button_action_funcs)

    def create_app_window_bindings(self):
        self._view.bind_reload_chapters(self._gui_controller.handle_reload_chapters)
        self._view.bind_clear_chapters(self._gui_controller.handle_clear_chapters)
        self._view.bind_select_player_shortcut(
            self._gui_controller.handle_connection_command
        )
        self._view.bind_save_chapters(
            self._gui_controller.handle_save_chapters_file_command
        )

    def build(self):
        self.create_menu_bar_bindings()
        chapters_title: str = ""
        chapters: Dict[str, str] = {}
        if self._chapters_filename:
            chapters_title, chapters = self._gui_controller.load_chapters_file(
                self._chapters_filename
            )
            dir = (Path(self._chapters_filename)).parent.absolute()
            self._view.set_chapters_file_path(str(dir))
        self.create_chapters_panel_bindings(chapters_title, chapters)
        self.create_player_control_panel_bindings()
        self.create_app_window_bindings()
        return self._view


def build_gui_menu(
    chapters_filename: str, mode: GuiMode = GuiMode.THEMED
) -> gui_classic.AppMainWindowClassic:
    running_players = PlayerFactory.get_running_player_names()
    player: Player = None
    try:
        if len(running_players) == 1:
            player_names = list(running_players.keys())
            selected_player_name = player_names[0]
            selected_player_fq_name = running_players[selected_player_name]
            logger.debug("Creating player")
            player = PlayerFactory.get_player(
                selected_player_fq_name, selected_player_name
            )

            logger.debug("Created player")
    except PlayerCreationError as e:
        print(e)
    gui_builder = AppGuiBuilder(chapters_filename, player, mode)
    gui_window = gui_builder.build()
    return gui_window
