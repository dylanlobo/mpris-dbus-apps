import logging
import tkinter as tk
from tkinter import ttk
from typing import List, Dict
from functools import partial
from .. import helpers as mpris_helpers
from ..helpers import Direction
from lib.dbus_mpris.core import NoValidMprisPlayersError, Player, PlayerFactory

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


def set_player_position(player: Player, position: str):
    player.set_position(mpris_helpers.to_microsecs(position))


def skip_player(player: Player, offset: str, direction: Direction = Direction.FORWARD):
    offset_with_dir = mpris_helpers.to_microsecs(offset) * direction
    player.seek(offset_with_dir)


def play_pause_player(player: Player):
    player.play_pause()


class ChaptersGui(tk.Tk):
    def __init__(self, media_title: str):
        super().__init__()
        self.title(media_title)

    def show_display(self):
        self.mainloop()


class ChaptersGuiBuilder:
    def __init__(self, chapters_filename: str, player: Player):
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

    @property
    def chapters_gui_window(self) -> ChaptersGui:
        return self._main_window

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


def build_gui_menu(chapters_filename: str, player: Player) -> ChaptersGui:
    gui_builder = ChaptersGuiBuilder(chapters_filename, player)
    gui_builder.build_chapters_panel()
    gui_builder.build_player_control_panel()
    return gui_builder.chapters_gui_window


if __name__ == "__main__":
    running_players = PlayerFactory.get_running_player_names()
    selected_player = mpris_helpers.get_selected_player(running_players)
    chapters_gui = build_gui_menu("ch.json", selected_player)
    chapters_gui.show_display()
