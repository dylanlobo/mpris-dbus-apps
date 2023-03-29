import logging
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from tkinter import ttk
from . import ch_icon as icon
from typing import List, Dict
from functools import partial
from ..helpers import Direction
from lib.dbus_mpris.core import PlayerProxy, PlayerFactory, PlayerCreationError
from .gui_controller import GuiController, AppInterface

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

    def set_chapters(self, chapters: List[str]):
        self._chapters_lb.delete(0, tk.END)
        self._chapters_lb.insert(tk.END, *chapters)

    def bind_chapters_selection_commands(
        self, chapters_selection_action_functs: List[callable]
    ):
        self._chapter_selection_action_functs = chapters_selection_action_functs

    def lb_selection_handler(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self._chapter_selection_action_functs[index]()


def ignore_arguments(func):
    """A decorator function that ignores all arguments and calls a function
    without any parameters. Useful in cases when a function is called via a
    callback that expects to call the function with one or more parameters
    that the pre-existing function does not require."""

    def decorator(self, *args, **kwargs):
        func()

    return decorator


class PlayerControlPanel(ttk.LabelFrame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, text="Player Controls")
        self._master = master
        self._buttons = []
        self._buttons.append(ttk.Button(self, text="<<<", width=6))
        self._buttons.append(ttk.Button(self, text="<<", width=6))
        self._buttons.append(ttk.Button(self, text="<", width=6))
        self._buttons.append(ttk.Button(self, text="Play/Pause"))
        self._buttons.append(ttk.Button(self, text=">", width=6))
        self._buttons.append(ttk.Button(self, text=">>", width=6))
        self._buttons.append(ttk.Button(self, text=">>>", width=6))
        self._init_button_to_key_dict()
        for i in range(len(self._buttons)):
            self._buttons[i].grid(row=0, column=(i + 1), padx=5, pady=10)
        self.grid(padx=10, pady=10)

    def _init_button_to_key_dict(self):
        self._button_to_key_dict = {
            "<<<": "<Control-Left>",
            "<<": "<Shift-Left>",
            "<": "<Left>",
            ">>>": "<Control-Right>",
            ">>": "<Shift-Right>",
            ">": "<Right>",
        }

    def bind_player_controls_commands(self, player_controls_funcs: Dict[str, callable]):
        for button in self._buttons:
            button_name = button.cget("text")
            button.configure(command=player_controls_funcs[button_name])
            if button_name in self._button_to_key_dict:
                self._master.bind(
                    self._button_to_key_dict[button_name],
                    ignore_arguments(player_controls_funcs[button_name]),
                )


class AppMenuBar(tk.Menu):
    def __init__(self, main_window: tk.Tk):
        super().__init__()
        self._main_window = main_window
        self._main_window.config(menu=self)

        self._connection_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Connect", menu=self._connection_menu)

        self._chapters_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Load Chapters", menu=self._chapters_menu)

    def bind_connect_to_player_command(self, connect_player_command: callable):
        self._connection_menu.add_command(
            label="Connect to player ...",
            command=connect_player_command,
        )

    def bind_load_chapters_file_command(self, load_chapters_file_command: callable):
        self._chapters_menu.add_command(
            label="Load chapters file ...", command=load_chapters_file_command
        )

    def bind_load_chapters_from_youtube_command(
        self, load_chapters_from_youtube_command: callable
    ):
        self._chapters_menu.add_command(
            label="Load chapters from Youtube ...",
            command=load_chapters_from_youtube_command,
        )


class AppMainWindow(tk.Tk):
    """The main window for the application. In addation, this class implements a view
    protocol (AppInterface) as part of an MVP implementation"""

    def __init__(self, media_title: str):
        super().__init__(className="Chapters")
        self.bind("<Escape>", self._handle_escape_pressed)
        self.title(media_title)
        icon.apply_icon(self)
        self.wm_title()
        self._menu_bar = AppMenuBar(self)
        self._chapters_listbox_items = []
        self._chapters_position_functions = []
        self._chapters_panel = ChaptersPanel(
            self,
            chapters=self._chapters_listbox_items,
            chapters_selection_action_functs=self._chapters_position_functions,
        )
        self._player_control_panel = PlayerControlPanel(self)
        self._chapters_file_path = None

    @property
    def menu_bar(self):
        return self._menu_bar

    @menu_bar.setter
    def menu_bar(self, menu_bar: AppMenuBar):
        self._menu_bar = menu_bar

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

    def _handle_escape_pressed(self, event):
        self.destroy()

    def show_display(self):
        self.grid()
        self.resizable(width=False, height=False)
        self.mainloop()

    def set_main_window_title(self, media_title: str):
        self.title(media_title)

    def set_chapters(self, chapters: List[str]):
        self._chapters_panel.set_chapters(chapters=chapters)

    def bind_chapters_selection_commands(
        self, chapters_selection_action_functs: List[callable]
    ):
        self._chapters_panel.bind_chapters_selection_commands(
            chapters_selection_action_functs=chapters_selection_action_functs
        )

    def bind_player_controls_commands(self, player_controls_funcs: Dict[str, callable]):
        self._player_control_panel.bind_player_controls_commands(player_controls_funcs)

    def bind_connect_to_player_command(self, connect_player_command: callable):
        self._menu_bar.bind_connect_to_player_command(connect_player_command)

    def bind_load_chapters_file_command(self, load_chapters_file_command: callable):
        self._menu_bar.bind_load_chapters_file_command(load_chapters_file_command)

    def bind_load_chapters_from_youtube_command(
        self, load_chapters_from_youtube_command: callable
    ):
        self._menu_bar.bind_load_chapters_from_youtube_command(
            load_chapters_from_youtube_command
        )

    def request_chapters_filename(self) -> str:
        if not self._chapters_file_path:
            self._chapters_file_path = f"{Path.home()}/Videos/Computing"
        if not Path(self._chapters_file_path).exists():
            self._chapters_file_path = f"{Path.home()}/Videos"
        if not Path(self._chapters_file_path).exists():
            self._chapters_file_path = f"{Path.home()}"
        selected_chapters_filename = filedialog.askopenfile(
            initialdir=self._chapters_file_path,
            title="Select Chapters file",
            filetypes=(("chapters files", "*.ch"),),
        )
        chapters_filename = ""
        if selected_chapters_filename:
            chapters_filename = selected_chapters_filename.name
            self._chapters_file_path = str(Path(chapters_filename).parent)
        return chapters_filename

    def select_new_player(self) -> PlayerProxy:
        running_player_names = PlayerFactory.get_running_player_names()
        self.popup = PlayerConnectionPopup(
            master=self, running_players=running_player_names
        )
        return self.popup.select_new_player()

    def get_youtube_video(self) -> str:
        self._yt_video_popup = YoutubeChaptersPopup(master=self)
        video = self._yt_video_popup.get_video()
        return video


class AppGuiBuilder:
    def __init__(self, chapters_filename: str, player: PlayerProxy):
        self._chapters_filename = chapters_filename
        self._player_control_panel: PlayerControlPanel = None
        self._chapters_panel: ChaptersPanel = None
        self._view: AppInterface = AppMainWindow("Chapters Player")
        if not player:
            self._player = PlayerProxy(None)
        else:
            self._player = player
        self._gui_controller = GuiController(self._view, self._player, self)

    @property
    def chapters_gui_window(self) -> AppMainWindow:
        return self._view

    @property
    def player(self) -> PlayerProxy:
        return self._player

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

    def create_chapters_panel_bindings(self):
        if self._chapters_filename:
            self._gui_controller.set_chapters_file(self._chapters_filename)
            self._gui_controller.set_listbox_items()

    def create_player_control_panel_bindings(self):
        button_action_funcs = {
            "Play/Pause": self._gui_controller.play_pause_player,
            ">": partial(self._gui_controller.skip_player, offset="00:00:05"),
            ">>": partial(self._gui_controller.skip_player, offset="00:00:10"),
            ">>>": partial(self._gui_controller.skip_player, offset="00:01:00"),
            "<": partial(
                self._gui_controller.skip_player,
                offset="00:00:05",
                direction=Direction.REVERSE,
            ),
            "<<": partial(
                self._gui_controller.skip_player,
                offset="00:00:10",
                direction=Direction.REVERSE,
            ),
            "<<<": partial(
                self._gui_controller.skip_player,
                offset="00:01:00",
                direction=Direction.REVERSE,
            ),
        }
        self._view.bind_player_controls_commands(button_action_funcs)


def build_gui_menu(chapters_filename: str, player: PlayerProxy) -> AppMainWindow:
    gui_builder = AppGuiBuilder(chapters_filename, player)
    gui_builder.create_menu_bar_bindings()
    gui_builder.create_chapters_panel_bindings()
    gui_builder.create_player_control_panel_bindings()
    return gui_builder.chapters_gui_window


class YoutubeChaptersPopup:
    def __init__(self, master: tk.Tk):
        self._video = ""
        self._master: tk.Tk = master
        self._video_name = tk.StringVar()

    def get_video(self) -> str:
        self._video_name_return = ""
        self._popup = tk.Toplevel(self._master)
        self._popup.title("Enter Youtube video id or url")
        self._create_video_entry_panel()
        self._popup.bind("<Return>", self._handle_enter_pressed)
        self._popup.bind("<Escape>", self._handle_escape_pressed)
        self._popup.bind("<Button-3>", self._handle_right_click_pressed)
        self._popup.resizable(width=False, height=False)
        self._popup.grid()
        # set to be on top of the main window
        self._popup.transient(self._master)
        # hijack all commands from the master (clicks on the main window are ignored)
        self._popup.grab_set()
        self._master.wait_window(
            self._popup
        )  # pause anything on the main window until this one closes
        return self._video_name_return

    def _create_video_entry_panel(self):
        self._input_panel = ttk.LabelFrame(
            master=self._popup, text="Youtube Video", width=50
        )
        self._video_name = tk.StringVar()
        self._video_name_entry = ttk.Entry(
            master=self._input_panel, textvariable=self._video_name
        )
        self._video_name_entry.grid(padx=5, pady=5)
        self._input_panel.grid(padx=5, pady=5)

        button_panel = ttk.Frame(master=self._popup)
        ok_button = ttk.Button(
            master=button_panel, text="OK", command=self._handle_ok_command
        )
        cancel_button = ttk.Button(
            master=button_panel, text="Cancel", command=self._handle_cancel_command
        )
        ok_button.grid(row=0, column=1, padx=10)
        cancel_button.grid(row=0, column=2, padx=10)
        ok_button.focus_force()
        button_panel.grid_columnconfigure(0, weight=1)
        button_panel.grid_rowconfigure(0, weight=1)
        button_panel.grid(padx=5, pady=5)

    def _handle_cancel_command(self):
        self._popup.destroy()

    def _handle_ok_command(self):
        self._video_name_return = self._video_name.get()
        self._popup.destroy()

    def _handle_enter_pressed(self, event):
        self._handle_ok_command()

    def _handle_escape_pressed(self, event):
        self._handle_cancel_command()

    def _handle_right_click_pressed(self, event):
        paste_text: str = self._master.clipboard_get()
        if paste_text:
            self._video_name.set(paste_text)


class PlayerConnectionPopup:
    def __init__(self, master: tk.Tk, running_players: Dict):
        self._master: tk.Tk = master
        self._running_players: Dict = running_players
        self._new_player: PlayerProxy = None

    def select_new_player(self) -> PlayerProxy:
        self._popup = tk.Toplevel(self._master)
        self._popup.title("Connect to Player")
        self._popup.bind("<Return>", self._handle_enter_pressed)
        self._popup.bind("<Escape>", self._handle_escape_pressed)
        self._running_players = self._running_players
        if not self._running_players:
            self._create_error_message_panel()
        else:
            self._create_players_selection_panel(list(self._running_players.keys()))
        self._popup.resizable(width=False, height=False)
        self._popup.grid()
        # set to be on top of the main window
        self._popup.transient(self._master)
        # hijack all commands from the master (clicks on the main window are ignored)
        self._popup.grab_set()
        self._master.wait_window(
            self._popup
        )  # pause anything on the main window until this one closes
        return self._new_player

    def _create_error_message_panel(self):
        message_panel = ttk.Frame(master=self._popup)
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
        players_panel = ttk.LabelFrame(master=self._popup, text="Players")
        lb_height = 5
        self._players_listbox = tk.Listbox(
            master=players_panel,
            listvariable=tk.StringVar(value=player_names),
            width=20,
            height=lb_height,
        )
        self._players_listbox.grid(column=0, row=0, sticky="NWES")
        self._players_listbox.select_set(0)
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

        button_panel = tk.Frame(master=self._popup)
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
        connect_button.focus_force()

    def _handle_connect_command(self):
        player_name = self._players_listbox.get(tk.ACTIVE)
        fq_player_name = self._running_players[player_name]
        if fq_player_name:
            try:
                self._new_player = PlayerFactory.get_player(fq_player_name, player_name)
            except PlayerCreationError as e:
                logger.error(e)
                # show a popup error here
        self._popup.destroy()

    def _handle_cancel_command(self):
        self._new_player = None
        self._popup.destroy()

    def _handle_ok_command(self):
        self._popup.destroy()

    def _handle_enter_pressed(self, event):
        self._handle_connect_command()

    def _handle_escape_pressed(self, event):
        self._handle_cancel_command()
