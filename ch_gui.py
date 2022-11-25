import tkinter as tk
from tkinter import ttk
from typing import List, Dict
from functools import partial
import lib.helpers as mpris_helpers
from lib.helpers import Direction
from lib.dbus_mpris.core import NoValidMprisPlayersError, Player, PlayerFactory


class ActionListBoxPanel(ttk.LabelFrame):

    def __init__(self, master=None, title: str = None, chapters: List[str] = None,
                 chapters_pos_funcs: List[callable] = None):
        super().__init__(master, text="Chapters")
        lb_height = len(chapters) if len(chapters) < 10 else 10
        lb = tk.Listbox(self, listvariable=tk.StringVar(value=chapters), width=60, height=lb_height)
        lb.grid(column=0, row=0, sticky="NWES")
        sv = ttk.Scrollbar(self, orient=tk.VERTICAL, command=lb.yview)
        sv.grid(column=1, row=0, sticky="NS")
        lb['yscrollcommand'] = sv.set
        sh = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=lb.xview)
        sh.grid(column=0, row=1, sticky="EW")
        lb['xscrollcommand'] = sh.set
        lb.bind("<<ListboxSelect>>", partial(ActionListBoxPanel.lb_selection_handler, func_list=ch_pos_func_list))
        # ttk.Sizegrip(self).grid(column=1, row=1, sticky="SE")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid()

    @staticmethod
    def lb_selection_handler(event, func_list: List[callable]):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            func_list[index]()


class PlayerControlPanel(ttk.LabelFrame):

    def __init__(self, master, player_controls_funcs: Dict[str, callable]):
        super().__init__(master, text="Player Controls")
        self.pause_play_button = ttk.Button(self, text="Play/Pause", command=player_controls_funcs["Play/Pause"])
        self.forward_30sec_button = ttk.Button(self, text=">", command=player_controls_funcs[">"])
        self.forward_1min_button = ttk.Button(self, text=">>", command=player_controls_funcs[">>"])
        self.backward_30sec_button = ttk.Button(self, text="<", command=player_controls_funcs["<"])
        self.backward_1min_button = ttk.Button(self, text="<<", command=player_controls_funcs["<<"])
        self.backward_1min_button.grid(row=0, column=1, padx=10, pady=10)
        self.backward_30sec_button.grid(row=0, column=2, padx=10)
        self.pause_play_button.grid(row=0, column=3, padx=10)
        self.forward_30sec_button.grid(row=0, column=4, padx=10)
        self.forward_1min_button.grid(row=0, column=5, padx=10)
        self.grid(padx=10, pady=10)


def set_player_postion(player: Player, position: str):
    player.set_position(mpris_helpers.to_microsecs(position))


def skip_player(player: Player, offset: str, direction: Direction = Direction.FORWARD):
    offset_with_dir = mpris_helpers.to_microsecs(offset) * direction
    player.seek(offset_with_dir)


def play_pause_player(player: Player):
    player.play_pause()


running_players = PlayerFactory.get_running_player_names()
selected_player = mpris_helpers.get_selected_player(running_players)
title, chapters_and_pos = mpris_helpers.load_chapters_file("ch.json")
listbox_items = []
i = 1
ch_list = []
ch_pos_func_list = []
for chapter, pos in chapters_and_pos.items():
    listbox_items.append(f"{i}.    {chapter} ({pos})")
    ch_list.append(chapter)
    ch_pos_func_list.append(partial(set_player_postion, selected_player, pos))
    i = i + 1

rt = tk.Tk()
rt.title(title)
alb = ActionListBoxPanel(rt, chapters=listbox_items)
funcs = {
    "Play/Pause": partial(play_pause_player, selected_player),
    ">": partial(skip_player, player=selected_player, offset="00:00:10"),
    ">>": partial(skip_player, player=selected_player, offset="00:01:00"),
    "<": partial(skip_player, player=selected_player, offset="00:00:10", direction=Direction.REVERSE),
    "<<": partial(skip_player, player=selected_player, offset="00:01:00", direction=Direction.REVERSE)
}
pc = PlayerControlPanel(rt, funcs)
