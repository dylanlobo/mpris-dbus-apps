from typing import Tuple, List, Dict, Protocol
from .. import helpers
from lib.dbus_mpris.core import PlayerProxy
import logging
from functools import partial

logger = logging.getLogger(__name__)


class AppGuiBuilderInterface(Protocol):
    def create_menu_bar_bindings(self):
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

    def get_youtube_video(self) -> str:
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

    def select_new_player(self) -> PlayerProxy:
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
        self._cur_player.set_position(helpers.to_microsecs(position))

    def skip_player(
        self, offset: str, direction: helpers.Direction = helpers.Direction.FORWARD
    ):
        offset_with_dir = helpers.to_microsecs(offset) * direction
        self._cur_player.seek(offset_with_dir)

    def play_pause_player(self):
        self._cur_player.play_pause()

    def handle_connection_command(self):
        new_player = self._view.select_new_player()
        if new_player:
            self.set_cur_player(new_player)

    def get_chapters_listbox_contents(
        self, chapters: Dict[str, str]
    ) -> Tuple[str, Dict[str, str], List[callable]]:
        listbox_items: List[str] = []
        chapters_position_functions: List[callable] = []
        chapter: str
        position: str
        if chapters:
            for index, (chapter, position) in enumerate(chapters.items()):
                listbox_items.append(f"{index+1}.    {chapter} ({position})")
                chapters_position_functions.append(
                    partial(self.set_player_position, position)
                )
        return (listbox_items, chapters_position_functions)

    def handle_load_chapters_file_command(self):
        chapters_title: str = ""
        chapters: Dict[str, str] = {}
        chapters_filename = self._view.request_chapters_filename()
        if not chapters_filename:
            return
        try:
            chapters_title, chapters = helpers.load_chapters_file(chapters_filename)
        except FileNotFoundError as fe:
            logger.error(fe)
            # TODO Implement and make call to view object to display error
            # message popup before returning
        except ValueError as ve:
            logger.error(ve)
            # TODO Implement and make call to view object to display error
            # message popup before returning
        (
            listbox_items,
            chapters_position_functions,
        ) = self.get_chapters_listbox_contents(chapters)
        self._view.set_main_window_title(chapters_title)
        self._view.set_chapters(chapters=listbox_items)
        self._view.bind_chapters_selection_commands(
            chapters_selection_action_functs=chapters_position_functions
        )

    def handle_load_chapters_from_youtube(self):
        video_name = self._view.get_youtube_video()
        if not video_name:
            return
        video_name = video_name.strip()
        if not video_name:
            return

        (chapters_title, chapters) = helpers.load_chapters_from_youtube(
            video=video_name
        )
        (
            listbox_items,
            chapters_position_functions,
        ) = self.get_chapters_listbox_contents(chapters)
        self._view.set_main_window_title(chapters_title)
        self._view.set_chapters(chapters=listbox_items)
        self._view.bind_chapters_selection_commands(
            chapters_selection_action_functs=chapters_position_functions
        )
