from typing import Tuple, List, Dict, Protocol
from .. import helpers as mpris_helpers
from ..helpers import Direction
from lib.dbus_mpris.core import PlayerProxy


class AppGuiBuilderInterface(Protocol):
    def create_menu_bar_bindings(self):
        ...

    def get_chapters_listbox_contents(
        self, chapters_filename: str, player: PlayerProxy
    ) -> Tuple[str, Dict[str, str], List[callable]]:
        ...

    def create_chapters_panel_bindings(self):
        ...

    def create_player_control_panel_bindings(self):
        ...


class AppInterface(Protocol):
    def set_main_window_title(self, media_title: str):
        ...

    def request_chapters_filename(self) -> str:
        ...

    def set_chapters(self, chapters: List[str]):
        ...

    def bind_chapters_selection_commands(
        self, chapters_selection_action_functs: List[callable]
    ):
        ...

    def bind_player_controls_commands(self, player_controls_funcs: Dict[str, callable]):
        ...

    def bind_connect_to_player_command(self, connect_player_command: callable):
        ...

    def request_player_selection(self, set_cur_player_func: callable):
        ...

    def bind_load_chapters_command(self, load_chapters_file_command: callable):
        ...

    def show_display(self):
        ...


class GuiController:
    def __init__(
        self,
        view: AppInterface,
        cur_player: PlayerProxy,
        app_gui_builder: AppGuiBuilderInterface,
    ):
        self._cur_player = cur_player
        self._view = view
        self._gui_builder = app_gui_builder
        self._chapters_file_path = None

    @property
    def cur_player(self):
        return self._cur_player

    def set_cur_player(self, player: PlayerProxy):
        self._cur_player = player

    @property
    def set_chapters_position_funcs(self):
        return self._chapter_position_funcs

    @set_chapters_position_funcs.setter
    def set_chapters_position_funcs(self, funcs_list: List[callable]):
        self.set_chapters_position_funcs = funcs_list

    def chapters_listbox_selection_handler(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self._chapter_selection_action_functs[index]()

    def set_player_position(self, position: str):
        self._cur_player.set_position(mpris_helpers.to_microsecs(position))

    def skip_player(self, offset: str, direction: Direction = Direction.FORWARD):
        offset_with_dir = mpris_helpers.to_microsecs(offset) * direction
        self._cur_player.seek(offset_with_dir)

    def play_pause_player(self):
        self._cur_player.play_pause()

    def handle_connection_command(self):
        self._view.request_player_selection(set_cur_player_func=self.set_cur_player)

    def handle_load_chapters_file_command(self):
        chapters_filename = self._view.request_chapters_filename()
        if not chapters_filename:
            return
        (
            chapters_title,
            chapters_listbox_contents,
            chapters_position_functions,
        ) = self._gui_builder.get_chapters_listbox_contents(
            chapters_filename.name, self.cur_player
        )
        self._view.set_main_window_title(chapters_title)
        self._view.set_chapters(chapters=chapters_listbox_contents)
        self._view.bind_chapters_selection_commands(
            chapters_selection_action_functs=chapters_position_functions
        )
