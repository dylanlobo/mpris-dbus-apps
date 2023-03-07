import logging
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from tkinter import ttk
from . import ch_icon as icon
from typing import Tuple, List, Dict, Protocol
from functools import partial
from .. import helpers as mpris_helpers
from ..helpers import Direction
from lib.dbus_mpris.core import PlayerProxy, PlayerFactory

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class ChaptersPanel(ttk.LabelFrame):
    def __init__(
        self,
        master: tk.Tk,
        chapters: List[str],
        chapters_selection_action_functs: List[callable],
    ):
        super().__init__(master, text="Chapters")
        self._chapters = chapters
        self._chapter_selection_action_functs = chapters_selection_action_functs
        # lb_height = len(chapters) if len(chapters) < 10 else 10
        lb_height = 10
        lb = tk.Listbox(
            self, listvariable=tk.StringVar(value=chapters), width=60, height=lb_height
        )
        self._chapters_lb = lb
        lb.grid(column=0, row=0, sticky="NWES")
        sv = ttk.Scrollbar(self, orient=tk.VERTICAL, command=lb.yview)
        sv.grid(column=1, row=0, sticky="NS")
        lb["yscrollcommand"] = sv.set
        sh = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=lb.xview)
        sh.grid(column=0, row=1, sticky="EW")
        lb["xscrollcommand"] = sh.set
        lb.bind("<<ListboxSelect>>", self.lb_selection_handler)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid()

    def set_chapters(
        self, chapters: List[str], chapters_selection_action_functs: List[callable]
    ):
        self._chapter_selection_action_functs = chapters_selection_action_functs
        self._chapters_lb.delete(0, tk.END)
        self._chapters_lb.insert(tk.END, *chapters)

    def lb_selection_handler(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self._chapter_selection_action_functs[index]()


class PlayerControlPanel(ttk.LabelFrame):
    def __init__(self, master: tk.Tk, player_controls_funcs: Dict[str, callable]):
        super().__init__(master, text="Player Controls")
        self.pause_play_button = ttk.Button(
            self, text="Play/Pause", command=player_controls_funcs["Play/Pause"]
        )
        self.forward_30sec_button = ttk.Button(
            self, text=">", command=player_controls_funcs[">"]
        )
        self.forward_1min_button = ttk.Button(
            self, text=">>", command=player_controls_funcs[">>"]
        )
        self.backward_30sec_button = ttk.Button(
            self, text="<", command=player_controls_funcs["<"]
        )
        self.backward_1min_button = ttk.Button(
            self, text="<<", command=player_controls_funcs["<<"]
        )
        self.backward_1min_button.grid(row=0, column=1, padx=10, pady=10)
        self.backward_30sec_button.grid(row=0, column=2, padx=10)
        self.pause_play_button.grid(row=0, column=3, padx=10)
        self.forward_30sec_button.grid(row=0, column=4, padx=10)
        self.forward_1min_button.grid(row=0, column=5, padx=10)
        self.grid(padx=10, pady=10)


class AppMainWindow(tk.Tk):
    """The main window for the application. In addation, this class implements a View
    protocol as part of an MVP implementation"""

    def __init__(self, media_title: str):
        super().__init__()
        self.title(media_title)
        icon.apply_icon(self)

    @property
    def chapters_panel(self):
        return self._chapters_panel

    @chapters_panel.setter
    def chapters_panel(self, chapters_panel: ChaptersPanel):
        self._chapters_panel = chapters_panel

    @property
    def player_control_panel(self):
        return self._player_control_panel

    @player_control_panel.setter
    def player_control_panel(self, player_control_panel: PlayerControlPanel):
        self._player_control_panel = player_control_panel

    def show_display(self):
        self.grid()
        self.resizable(width=False, height=False)
        self.mainloop()

    def set_main_window_title(self, media_title: str):
        self.title(media_title)

    def set_chapters(
        self, chapters: List[str], chapters_selection_action_functs: List[callable]
    ):
        self._chapters_panel.set_chapters(
            chapters=chapters,
            chapters_selection_action_functs=chapters_selection_action_functs,
        )


class AppGuiBuilder:
    def __init__(self, chapters_filename: str, player: PlayerProxy):
        self._chapters_filename = chapters_filename
        self._player_control_panel: PlayerControlPanel = None
        self._chapters_panel: ChaptersPanel = None
        self._main_window = AppMainWindow("Chapters Player")
        self._player = player
        self._gui_controller = GuiController(self._main_window, self._player, self)

    @property
    def chapters_gui_window(self) -> AppMainWindow:
        return self._main_window

    @property
    def player(self) -> PlayerProxy:
        return self._player

    def build_menu_bar(self):
        menu_bar = tk.Menu(master=self._main_window)
        self._main_window.config(menu=menu_bar)

        connection_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Connect", menu=connection_menu)
        connection_menu.add_command(
            label="Connect to player ...",
            command=self._gui_controller.handle_connection_command,
        )

        chapters_menu = tk.Menu(menu_bar, tearoff=0)
        chapters_menu.add_command(
            label="Select chapters file ...",
            command=self._gui_controller.handle_load_chapters_file_command,
        )
        menu_bar.add_cascade(label="Load Chapters", menu=chapters_menu)

    def get_chapters_listbox_contents(
        self, chapters_filename: str, player: PlayerProxy
    ) -> Tuple[str, Dict[str, str], List[callable]]:
        chapters_title: str = None
        chapters: Dict[str, str] = None
        try:
            chapters_title, chapters = mpris_helpers.load_chapters_file(
                chapters_filename
            )
        except FileNotFoundError as fe:
            logger.error(fe)
            raise fe
        listbox_items: List[str] = []
        chapters_position_functions: List[callable] = []
        chapter: str
        position: str
        for index, (chapter, position) in enumerate(chapters.items()):
            listbox_items.append(f"{index+1}.    {chapter} ({position})")
            chapters_position_functions.append(
                partial(self._gui_controller.set_player_position, position)
            )
        return (chapters_title, listbox_items, chapters_position_functions)

    def build_chapters_panel(self):
        (
            self._chapters_title,
            self._chapters_listbox_items,
            self._chapters_position_functions,
        ) = self.get_chapters_listbox_contents(self._chapters_filename, self._player)
        self._main_window.title(self._chapters_title)
        self._main_window.chapters_panel = ChaptersPanel(
            self._main_window,
            chapters=self._chapters_listbox_items,
            chapters_selection_action_functs=self._chapters_position_functions,
        )

    def build_player_control_panel(self):
        button_action_funcs = {
            "Play/Pause": partial(self._gui_controller.play_pause_player),
            ">": partial(self._gui_controller.skip_player, offset="00:00:10"),
            ">>": partial(self._gui_controller.skip_player, offset="00:01:00"),
            "<": partial(
                self._gui_controller.skip_player,
                offset="00:00:10",
                direction=Direction.REVERSE,
            ),
            "<<": partial(
                self._gui_controller.skip_player,
                offset="00:01:00",
                direction=Direction.REVERSE,
            ),
        }
        self._main_window.player_control_panel = PlayerControlPanel(
            self._main_window, button_action_funcs
        )


def build_gui_menu(chapters_filename: str, player: PlayerProxy) -> AppMainWindow:
    gui_builder = AppGuiBuilder(chapters_filename, player)
    gui_builder.build_menu_bar()
    gui_builder.build_chapters_panel()
    gui_builder.build_player_control_panel()
    return gui_builder.chapters_gui_window


class PlayerConnectionPopup(tk.Toplevel):
    def __init__(self, master: tk.Tk, running_players: Dict, set_cur_player: callable):
        super().__init__(master)
        self._set_cur_player = set_cur_player
        self.title("Connect to Player")
        self._running_players = running_players
        if not self._running_players:
            self._create_error_message_panel()
        else:
            self._create_players_selection_panel(list(self._running_players.keys()))
        self.resizable(width=False, height=False)
        self.grid()
        # set to be on top of the main window
        self.transient(master)
        # hijack all commands from the master (clicks on the main window are ignored)
        self.grab_set()
        master.wait_window(
            self
        )  # pause anything on the main window until this one closes

    def _create_error_message_panel(self):
        message_panel = ttk.Frame(master=self)
        message = ttk.Label(
            master=message_panel,
            text="No MPRIS enabled media players are currently running!",
        )
        ok_button = ttk.Button(
            master=message_panel, text="OK", command=self._handle_ok_command
        )
        message.grid(row=0, column=0, padx=5, pady=5)
        ok_button.grid(row=1, column=0, padx=10, pady=5)
        message_panel.grid()

    def _create_players_selection_panel(self, player_names: List):
        players_panel = ttk.LabelFrame(master=self, text="Players")
        lb_height = 5
        self._players_listbox = tk.Listbox(
            master=players_panel,
            listvariable=tk.StringVar(value=player_names),
            width=20,
            height=lb_height,
        )
        self._players_listbox.grid(column=0, row=0, sticky="NWES")
        sv = ttk.Scrollbar(
            players_panel, orient=tk.VERTICAL, command=self._players_listbox.yview
        )
        sv.grid(column=1, row=0, sticky="NS")
        self._players_listbox["yscrollcommand"] = sv.set
        sh = ttk.Scrollbar(
            players_panel, orient=tk.HORIZONTAL, command=self._players_listbox.xview
        )
        sh.grid(column=0, row=1, sticky="EW")
        self._players_listbox["xscrollcommand"] = sh.set
        players_panel.grid_columnconfigure(0, weight=1)
        players_panel.grid_rowconfigure(0, weight=1)
        players_panel.grid(padx=0, pady=5)

        button_panel = tk.Frame(master=self)
        connect_button = ttk.Button(
            master=button_panel, text="Connect", command=self._handle_connect_command
        )
        cancel_button = ttk.Button(
            master=button_panel, text="Cancel", command=self._handle_cancel_command
        )
        connect_button.grid(row=0, column=1, padx=10)
        cancel_button.grid(row=0, column=2, padx=10)
        button_panel.grid_columnconfigure(0, weight=1)
        button_panel.grid_rowconfigure(0, weight=1)
        button_panel.grid(pady=10)

    def _handle_connect_command(self):
        player_name = self._players_listbox.get(tk.ACTIVE)
        fq_player_name = self._running_players[player_name]
        new_player = None
        if fq_player_name:
            new_player = PlayerFactory.get_player(fq_player_name, player_name)
            self._set_cur_player(new_player)
        self.destroy()

    def _handle_cancel_command(self):
        self.destroy()

    def _handle_ok_command(self):
        self.destroy()


class View(Protocol):
    def get_main_window(self) -> tk.Tk:
        ...

    def set_main_window_title(self, media_title: str):
        ...

    def set_chapters(
        self, chapters: List[str], chapters_selection_action_functs: List[callable]
    ):
        ...

    def show_display(self):
        ...


class GuiController:
    def __init__(
        self, view: View, cur_player: PlayerProxy, app_gui_builder: AppGuiBuilder
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
        running_player_names = PlayerFactory.get_running_player_names()
        self.popup = PlayerConnectionPopup(
            master=AppGuiBuilder.main_window,
            running_players=running_player_names,
            set_cur_player=self.set_cur_player,
        )

    def handle_load_chapters_file_command(self):
        if not self._chapters_file_path:
            self._chapters_file_path = f"{Path.home()}/Videos"
            if not Path(self._chapters_file_path).exists():
                self._chapters_file_path = f"{Path.home()}"
        chapters_filename = filedialog.askopenfile(
            initialdir=self._chapters_file_path,
            title="Select Chapters file",
            filetypes=(("chapters files", "*.json"),),
        )
        if not chapters_filename:
            return
        self._chapters_file_path = str(Path(chapters_filename.name).parent)
        (
            chapters_title,
            chapters_listbox_contents,
            chapters_position_functions,
        ) = self._gui_builder.get_chapters_listbox_contents(
            chapters_filename.name, self.cur_player
        )
        self._view.set_main_window_title(chapters_title)
        self._view.set_chapters(
            chapters=chapters_listbox_contents,
            chapters_selection_action_functs=chapters_position_functions,
        )
