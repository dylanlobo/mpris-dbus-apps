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

    def set_player_instance_name(self, instance_name):
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

    def bind_reload_chapters(self, reload_chapters: callable):
        ...

    def bind_clear_chapters(self, clear_chapters: callable):
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
        self._view = view
        self._gui_builder = app_gui_builder
        self.cur_player = cur_player
        self._initialiase_chapters_content()

    def _initialiase_chapters_content(self):
        self._chapters_file_name: str = ""
        self._chapters_yt_video: str = ""
        self._chapters_title: str = "Chapters Player"
        self._chapters: Dict[str, str] = {}

    @property
    def cur_player(self):
        return self._cur_player

    @cur_player.setter
    def cur_player(self, player: PlayerProxy):
        self._cur_player = player
        self._view.set_player_instance_name(player.ext_name)

    @property
    def chapters_position_funcs(self):
        return self._chapter_position_funcs

    @chapters_position_funcs.setter
    def chapters_position_funcs(self, funcs_list: List[callable]):
        self._chapters_position_funcs = funcs_list

    def set_chapters_file(self, filename: str):
        self._chapters_file_name = filename
        self._load_chapters_file()

    def _load_chapters_file(self):
        try:
            self._chapters_title, self._chapters = helpers.load_chapters_file(
                self._chapters_file_name
            )
        except Exception as e:
            logger.error(e)
            raise e

    def set_chapters_yt_video(self, video: str):
        self._chapters_yt_video = video
        self._load_chapters_from_youtube()

    def _load_chapters_from_youtube(self):
        try:
            (self._chapters_title, self._chapters) = helpers.load_chapters_from_youtube(
                video=self._chapters_yt_video
            )
        except Exception as e:
            logger.error(e)
            raise e

    def set_listbox_items(self):
        (
            listbox_items,
            chapters_position_functions,
        ) = self.get_chapters_listbox_contents()
        self._view.set_main_window_title(self._chapters_title)
        self._view.set_chapters(chapters=listbox_items)
        self._view.bind_chapters_selection_commands(
            chapters_selection_action_functs=chapters_position_functions
        )

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

    def next_player(self):
        self._cur_player.next()

    def previous_player(self):
        self._cur_player.previous()

    def handle_connection_command(self):
        new_player = self._view.select_new_player()
        if new_player:
            self.cur_player = new_player

    def get_chapters_listbox_contents(
        self,
    ) -> Tuple[str, Dict[str, str], List[callable]]:
        listbox_items: List[str] = []
        chapters_position_functions: List[callable] = []
        chapter: str
        position: str
        if self._chapters:
            for index, (chapter, position) in enumerate(self._chapters.items()):
                listbox_items.append(f"{index+1}.    {chapter} ({position})")
                chapters_position_functions.append(
                    partial(self.set_player_position, position)
                )
        return (listbox_items, chapters_position_functions)

    def handle_load_chapters_file_command(self):
        chapters_filename = self._view.request_chapters_filename()
        if not chapters_filename:
            return
        try:
            self.set_chapters_file(chapters_filename)
        except (FileNotFoundError, ValueError) as e:
            logger.error(e)
            # TODO Implement and make call to view object to display error
            # message popup before returning
            return
        self.set_listbox_items()

    def handle_load_chapters_from_youtube(self):
        video_name = self._view.get_youtube_video()
        if not video_name:
            return
        video_name = video_name.strip()
        if not video_name:
            return
        try:
            self.set_chapters_yt_video(video_name)
        except Exception as e:
            logger.error(e)
            # TODO Implement and make call to view object to display error
            # message popup before returning
            return
        self.set_listbox_items()

    def handle_reload_chapters(self, event):
        if self._chapters_file_name:
            try:
                self.set_chapters_file(self._chapters_file_name)
            except (FileNotFoundError, ValueError) as e:
                logger.error(e)
                # TODO Implement and make call to view object to display error
                # message popup before returning
                return
            self.set_listbox_items()

    def handle_clear_chapters(self, event):
        self._initialiase_chapters_content()
        self.set_listbox_items()
