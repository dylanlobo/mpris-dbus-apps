import logging
import tkinter as tk
from tkinter import ttk
from typing import List, Dict
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
        lb_height = len(chapters) if len(chapters) < 10 else 10
        lb = tk.Listbox(
            self, listvariable=tk.StringVar(value=chapters), width=60, height=lb_height
        )
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


def set_player_position(player: PlayerProxy, position: str):
    player.set_position(mpris_helpers.to_microsecs(position))


def skip_player(
    player: PlayerProxy, offset: str, direction: Direction = Direction.FORWARD
):
    offset_with_dir = mpris_helpers.to_microsecs(offset) * direction
    player.seek(offset_with_dir)


def play_pause_player(player: PlayerProxy):
    player.play_pause()


class ChaptersGui(tk.Tk):
    def __init__(self, media_title: str):
        super().__init__()
        self.title(media_title)

    def show_display(self):
        self.grid()
        self.resizable(width=False, height=False)
        self.mainloop()

    @property
    def root_window(self):
        return self._root


class PlayerConnectionPopup(tk.Toplevel):
    def __init__(self, master: tk.Tk, running_players: Dict):
        super().__init__(master)
        self.title("Connect to Player")
        self._running_players = running_players
        if not self._running_players:
            self._create_error_message_panel()
        else:
            self._create_players_selection_panel(list(self._running_players.keys()))
        self.resizable(width=False, height=False)
        self.grid()
        self.transient(master)  # set to be on top of the main window
        self.grab_set()  # hijack all commands from the master (clicks on the main window are ignored)
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

        # button_panel = ttk.LabelFrame(master=self)
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
            ChaptersGuiBuilder.current_player.set_player(new_player)
        self.destroy()

    def _handle_cancel_command(self):
        self.destroy()

    def _handle_ok_command(self):
        self.destroy()


def handle_connection_command():
    running_player_names = PlayerFactory.get_running_player_names()
    popup = PlayerConnectionPopup(
        master=ChaptersGuiBuilder.main_window,
        running_players=running_player_names,
    )


class ChaptersGuiBuilder:
    main_window: tk.Tk = None
    current_player: PlayerProxy = None

    def __init__(self, chapters_filename: str, player: PlayerProxy):
        self._player_control_panel: PlayerControlPanel = None
        self._chapters_panel: ChaptersPanel = None
        self._player = player
        try:
            self._chapters_title, self._chapters = mpris_helpers.load_chapters_file(
                chapters_filename
            )
        except FileNotFoundError as fe:
            logger.error(fe)
            raise fe
        self._main_window = ChaptersGui(self._chapters_title)
        ChaptersGuiBuilder.main_window = self._main_window
        ChaptersGuiBuilder.current_player = self._player

    @property
    def chapters_gui_window(self) -> ChaptersGui:
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
            label="Connect to ...", command=handle_connection_command
        )

    def build_chapters_panel(self):
        listbox_items: List[str] = []
        chapters_position_functions: List[callable] = []
        chapter: str
        position: str
        for index, (chapter, position) in enumerate(self._chapters.items()):
            listbox_items.append(f"{index+1}.    {chapter} ({position})")
            chapters_position_functions.append(
                partial(set_player_position, self._player, position)
            )
        self._chapters_panel = ChaptersPanel(
            self._main_window,
            chapters=listbox_items,
            chapters_selection_action_functs=chapters_position_functions,
        )

    def build_player_control_panel(self):
        button_action_funcs = {
            "Play/Pause": partial(play_pause_player, self._player),
            ">": partial(skip_player, player=self._player, offset="00:00:10"),
            ">>": partial(skip_player, player=self._player, offset="00:01:00"),
            "<": partial(
                skip_player,
                player=self._player,
                offset="00:00:10",
                direction=Direction.REVERSE,
            ),
            "<<": partial(
                skip_player,
                player=self._player,
                offset="00:01:00",
                direction=Direction.REVERSE,
            ),
        }
        self._player_control_panel = PlayerControlPanel(
            self._main_window, button_action_funcs
        )


def build_gui_menu(chapters_filename: str, player: PlayerProxy) -> ChaptersGui:
    gui_builder = ChaptersGuiBuilder(chapters_filename, player)
    gui_builder.build_menu_bar()
    gui_builder.build_chapters_panel()
    gui_builder.build_player_control_panel()
    return gui_builder.chapters_gui_window
