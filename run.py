import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys

import shelling

# Folder/file icons (using Unicode symbols)
FOLDER_ICON = "📁"
FILE_ICON = "📄"
CHECKED_BOX = "☑"
UNCHECKED_BOX = "☐"

# Detect if running as PyInstaller exe
if getattr(sys, 'frozen', False):
    # For bundled resources (read-only)
    PROGRAM_BASE_PATH = sys._MEIPASS
    # For user data (writable) - use AppData folder
    import tempfile
    user_data_dir = os.path.join(os.path.expanduser("~"), ".nopaste")
    os.makedirs(user_data_dir, exist_ok=True)
    SETTINGS_FILE = os.path.join(user_data_dir, "settings.json")
else:
    PROGRAM_BASE_PATH = os.path.abspath(".")
    SETTINGS_FILE = os.path.join(PROGRAM_BASE_PATH, "settings.json")

# Colors
BG = "#07050b"  # (#110d1b) very dark with slight purple tint
ACCENT = "#4b1168"  # dark purple accent
CARD = "#0f0813"  # slightly lighter card background
FG = "#e9e6f1"  # light foreground

FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 10, "bold")



class MyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NoPaste C++ Compiler")
        icon_path = os.path.join(PROGRAM_BASE_PATH, "skull.ico")
        self.iconbitmap(icon_path)
        self.configure(bg=BG)
        self.geometry("900x560")
        self.minsize(820, 480)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.settings_path = SETTINGS_FILE
        self._loading_settings = False

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # General ttk styles
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD, borderwidth=1, relief="flat")

        # Buttons
        style.configure("Accent.TButton", background=ACCENT, foreground=FG, font=FONT_BUTTON, relief="flat")
        style.map("Accent.TButton",
                  background=[('active', ACCENT)],
                  foreground=[('disabled', '#777')])

        style.configure("Card.TButton", background=CARD, foreground=FG, font=FONT_BUTTON, relief="flat")
        style.map("Card.TButton",
                  background=[('active', CARD)],
                  foreground=[('disabled', '#777')])

        # Entry / Combobox
        style.configure("Card.TEntry", fieldbackground=CARD, foreground=FG)
        style.configure("TCombobox", fieldbackground=CARD, background=CARD, foreground=FG,
                        selectbackground=CARD, selectforeground=FG)
        style.map("TCombobox",
                  fieldbackground=[('readonly', CARD)],
                  selectbackground=[('readonly', CARD)],
                  selectforeground=[('readonly', FG)])

        # Checkbutton
        style.configure("Card.TCheckbutton", background=CARD, foreground=FG)
        style.map("Card.TCheckbutton",
                  background=[('active', CARD)])

        # Folder/File labels with hover effect
        style.configure("Folder.TLabel", background=CARD, foreground=FG, font=FONT_LABEL)
        style.map("Folder.TLabel",
                  background=[('active', CARD)],
                  foreground=[('active', 'white')])

        # Scrollbar
        style.element_create("Custom.Vertical.Scrollbar.trough", "from", "clam")
        style.configure("Vertical.TScrollbar", troughcolor=CARD, background=ACCENT, bordercolor=CARD, arrowcolor=FG,
                        gripcount=0)

        # Treeview (file explorer)
        style.configure(
            "NoPaste.Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=FG,
            bordercolor=BG,
            borderwidth=0,
            rowheight=26,
            font=FONT_LABEL
        )
        style.map(
            "NoPaste.Treeview",
            background=[('selected', ACCENT)],
            foreground=[('selected', FG)]
        )
        style.configure("NoPaste.Treeview.Heading", background=ACCENT, foreground=FG, font=FONT_BUTTON, borderwidth=0)

        # Labels
        style.configure("TLabel", background=BG, foreground=FG, font=FONT_LABEL)
        style.configure("Card.TLabel", background=CARD, foreground=FG, font=FONT_LABEL)

        # Top title bar
        # title_bar = ttk.Frame(self, style="Card.TFrame")
        # title_bar.pack(fill="x", padx=10, pady=10)
        # title_label = ttk.Label(title_bar, text="NoPaste", font=("Segoe UI", 14, "bold"), background=CARD, foreground=FG)
        # title_label.pack(side="left", padx=8, pady=6)

        # main area
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Left column: Select directory and file tree
        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 12), pady=6)

        select_btn = ttk.Button(left, text="Select directory", command=self.select_directory, style="Card.TButton")
        select_btn.pack(anchor="nw", pady=(6, 10))

        self.file_tree_card = ttk.Frame(left, style="Card.TFrame")
        self.file_tree_card.pack(fill="both", expand=True, ipadx=6, ipady=6)
        self.file_tree_card.configure(width=360, height=420)

        self.tree = ttk.Treeview(
            self.file_tree_card,
            columns=("path", "type"),
            show="tree",
            selectmode="extended",
            style="NoPaste.Treeview"
        )
        self.tree.heading("#0", text="Project files", anchor="w")
        self.tree.column("#0", stretch=True)
        self.tree.column("path", width=0, stretch=False)
        self.tree.column("type", width=0, stretch=False)

        tree_scrollbar = ttk.Scrollbar(
            self.file_tree_card,
            orient="vertical",
            command=self.tree.yview,
            style="Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.tree.bind("<Button-1>", self.on_tree_click, add="+")
        self.tree.bind("<space>", self.on_space_toggle)

        self.root_directory = None
        self.root_id = None
        self.loaded_nodes = set()
        self.checked_state = {}
        self.node_names = {}
        self.path_to_id = {}

        # Right column: options & actions
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        # Top options row
        options_row = ttk.Frame(right)
        options_row.pack(fill="x", pady=(6, 20))

        # C++ standard dropdown
        std_label = ttk.Label(options_row, text="c++ standard version", style="Card.TLabel", background=CARD)
        std_label.grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.cpp_standard = tk.StringVar(value="c++17")
        self.cpp_standard.trace_add("write", self._on_state_change)
        self.standards = ["c++98", "c++11", "c++14", "c++17", "c++20", "c++23"]
        self.std_combo = ttk.Combobox(
            options_row,
            values=self.standards,
            textvariable=self.cpp_standard,
            state="readonly",
            width=12,
        )
        # Configure the combobox colors
        self.std_combo.grid(row=1, column=0, sticky="w", padx=(0, 6))
        # Fix combobox dropdown background
        self.option_add('*TCombobox*Listbox.background', CARD)
        self.option_add('*TCombobox*Listbox.foreground', FG)
        self.option_add('*TCombobox*Listbox.selectBackground', ACCENT)
        self.option_add('*TCombobox*Listbox.selectForeground', FG)

        # Another dropdown with checkboxes (opens popup)
        self.opt_btn = ttk.Button(options_row, text="Options...", command=self.open_options_popup, style="Card.TButton")
        self.opt_btn.grid(row=1, column=1, padx=(20, 6))

        # Placeholder spacer
        options_row.columnconfigure(2, weight=1)

        # Output name entry
        out_frame = ttk.Frame(right)
        out_frame.pack(fill="x", pady=(20, 12))
        out_label = ttk.Label(out_frame, text='Output file name:', style="Card.TLabel", background=CARD)
        out_label.pack(anchor="w")
        self.output_name = tk.StringVar(value="a.out")
        out_entry = ttk.Entry(out_frame, textvariable=self.output_name, style="Card.TEntry")
        out_entry.pack(fill="x", pady=(6, 0))

        # Bottom action buttons
        action_frame = ttk.Frame(right)
        action_frame.pack(side="bottom", anchor="e", pady=12)

        compile_btn = ttk.Button(action_frame, text="Compile", command=self.compile_action, style="Accent.TButton")
        compile_btn.pack(side="left", padx=(0, 10))
        
        # Run button with dropdown
        run_frame = ttk.Frame(action_frame)
        run_frame.pack(side="left")
        
        self.run_mode = tk.StringVar(value="run")
        self.run_mode.trace_add("write", self._on_run_mode_change)
        self.run_modes = ["run", "run valgrind"]
        
        self.run_btn = ttk.Button(run_frame, text="Run program", command=self.run_action, style="Card.TButton")
        self.run_btn.pack(side="left")
        
        run_dropdown_btn = ttk.Button(run_frame, text="▼", command=self.show_run_menu, style="Card.TButton", width=3)
        run_dropdown_btn.pack(side="left", padx=(2, 0))

        # state for options popup
        self.options = {
            "Optimize": tk.BooleanVar(value=False),
            "Warn All": tk.BooleanVar(value=True),
            "Debug info": tk.BooleanVar(value=True),
            "Warnings as errors": tk.BooleanVar(value=False),
            "Link static": tk.BooleanVar(value=False),
        }
        for var in self.options.values():
            var.trace_add("write", self._on_state_change)

        self.load_settings()

    def select_directory(self):
        folder = filedialog.askdirectory()
        print("selected directory: ", folder)
        if folder:
            self.populate_file_tree(folder)
            self._on_state_change()

    def clear_file_tree(self):
        for child in self.tree.get_children():
            self.tree.delete(child)
        self.loaded_nodes.clear()
        self.root_directory = None
        self.root_id = None
        self.checked_state.clear()
        self.node_names.clear()
        self.path_to_id.clear()

    def populate_file_tree(self, root_dir: str):
        if not root_dir:
            return

        self.clear_file_tree()
        normalized_root = os.path.normpath(root_dir)
        self.root_directory = normalized_root

        root_name = os.path.basename(normalized_root) or normalized_root
        root_id = self.tree.insert("", "end", text=root_name, values=(normalized_root, "dir"), open=True)
        self.root_id = root_id
        self.node_names[root_id] = root_name
        self.path_to_id[normalized_root] = root_id
        self._set_check_state(root_id, False)
        self._add_placeholder(root_id)
        self._load_children(root_id, normalized_root)
        self.loaded_nodes.add(root_id)
        self.tree.selection_set(root_id)
        self.tree.focus(root_id)

    def _add_placeholder(self, parent_id: str):
        # Placeholder child so Treeview shows an expand arrow
        self.tree.insert(parent_id, "end", text="loading...", values=("", "placeholder"))

    def _load_children(self, parent_id: str, directory: str):
        # Remove placeholder rows
        for child in self.tree.get_children(parent_id):
            if self.tree.set(child, "type") == "placeholder":
                self.tree.delete(child)

        try:
            entries = list(os.scandir(directory))
        except PermissionError:
            messagebox.showwarning("Permission denied", f"Cannot access {directory}")
            return
        except FileNotFoundError:
            return

        entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))

        for entry in entries:
            node_type = "dir" if entry.is_dir() else "file"
            node_path = os.path.normpath(entry.path)
            child_id = self.tree.insert(
                parent_id,
                "end",
                text=entry.name,
                values=(node_path, node_type),
                open=False
            )
            self.node_names[child_id] = entry.name
            self.path_to_id[node_path] = child_id
            parent_checked = self.checked_state.get(parent_id, False)
            self._set_check_state(child_id, parent_checked)
            if entry.is_dir():
                self._add_placeholder(child_id)

    def _format_item_text(self, name: str, node_type: str, checked: bool) -> str:
        icon = FOLDER_ICON if node_type == "dir" else FILE_ICON
        box = CHECKED_BOX if checked else UNCHECKED_BOX
        return f"{box} {icon} {name}"

    def _set_check_state(self, item_id: str, checked: bool, propagate_children: bool = False):
        self.checked_state[item_id] = checked
        node_type = self.tree.set(item_id, "type")
        if not node_type or node_type == "placeholder":
            return
        name = self.node_names.get(item_id, self.tree.item(item_id, "text"))
        self.tree.item(item_id, text=self._format_item_text(name, node_type, checked))

        if propagate_children and node_type == "dir":
            for child in self.tree.get_children(item_id):
                self._set_check_state(child, checked, propagate_children=True)

    def _toggle_item_check(self, item_id: str):
        current = self.checked_state.get(item_id, False)
        node_type = self.tree.set(item_id, "type")
        propagate = node_type == "dir"
        self._set_check_state(item_id, not current, propagate_children=propagate)
        self._on_state_change()

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "tree":
            return
        element = self.tree.identify("element", event.x, event.y)
        if element == "Treeitem.indicator":
            return
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        self._toggle_item_check(item_id)

    def on_space_toggle(self, _event):
        item_id = self.tree.focus()
        if not item_id:
            return
        self._toggle_item_check(item_id)

    def on_tree_open(self, _event):
        item_id = self.tree.focus()
        if not item_id or item_id in self.loaded_nodes:
            return

        node_type = self.tree.set(item_id, "type")
        path = self.tree.set(item_id, "path")
        if node_type == "dir" and path:
            self._load_children(item_id, path)
            self.loaded_nodes.add(item_id)

    def _collect_files_under(self, directory: str) -> list[str]:
        collected: list[str] = []
        for root, _dirs, files in os.walk(directory):
            for filename in files:
                collected.append(os.path.join(root, filename))
        return collected

    def _gather_checked_paths(self) -> list[str]:
        if not self.root_directory:
            return []
        seen = set()
        paths: list[str] = []
        for item_id, checked in self.checked_state.items():
            if not checked:
                continue
            path = self.tree.set(item_id, "path")
            if not path:
                continue
            normalized = os.path.normpath(path)
            if normalized in seen:
                continue
            seen.add(normalized)
            paths.append(normalized)
        return paths

    def _ensure_node_for_path(self, path: str):
        if not self.root_directory or not path:
            return None
        normalized = os.path.normpath(path)
        root_norm = os.path.normpath(self.root_directory)
        try:
            if os.path.commonpath([root_norm, normalized]) != root_norm:
                return None
        except ValueError:
            return None

        if normalized == root_norm:
            return self.root_id

        if normalized in self.path_to_id:
            return self.path_to_id[normalized]

        parent_path = os.path.dirname(normalized)
        if not parent_path or parent_path == normalized:
            return None

        parent_id = self._ensure_node_for_path(parent_path)
        if not parent_id:
            return None

        parent_dir = self.tree.set(parent_id, "path")
        if not parent_dir or self.tree.set(parent_id, "type") != "dir":
            return None

        self._load_children(parent_id, parent_dir)
        self.loaded_nodes.add(parent_id)
        self.tree.item(parent_id, open=True)
        return self.path_to_id.get(normalized)

    def _restore_checked_paths(self, paths: list[str]):
        if not paths:
            return
        for path in paths:
            if not path or not os.path.exists(path):
                continue
            item_id = self._ensure_node_for_path(path)
            if item_id:
                self._set_check_state(item_id, True)

    def _on_state_change(self, *_args):
        if self._loading_settings:
            return
        self.save_settings()

    def save_settings(self):
        data = {
            "root_directory": self.root_directory,
            "checked_paths": self._gather_checked_paths(),
            "cpp_standard": self.cpp_standard.get(),
            "options": {k: v.get() for k, v in self.options.items()},
            "output_file_name": self.output_name.get()
        }
        try:
            with open(self.settings_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
        except OSError as exc:
            print(f"Failed to save settings: {exc}")

    def load_settings(self):
        if not os.path.exists(self.settings_path):
            return
        try:
            with open(self.settings_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Failed to load settings: {exc}")
            return

        self._loading_settings = True
        try:
            self.output_name.set(data.get("output_file_name"))
            saved_std = data.get("cpp_standard")
            if isinstance(saved_std, str) and saved_std in self.standards:
                self.cpp_standard.set(saved_std)

            saved_options = data.get("options", {})
            if isinstance(saved_options, dict):
                for name, var in self.options.items():
                    var.set(bool(saved_options.get(name, False)))

            root_dir = data.get("root_directory")
            checked_paths = data.get("checked_paths", [])
            if isinstance(root_dir, str) and os.path.isdir(root_dir):
                self.populate_file_tree(root_dir)
                if isinstance(checked_paths, list):
                    self._restore_checked_paths(checked_paths)
        finally:
            self._loading_settings = False

    def on_close(self):
        self.save_settings()
        self.destroy()

    def open_options_popup(self):
        win = tk.Toplevel(self)
        win.title("Options")
        win.configure(bg=BG)
        win.geometry("260x220")
        win.transient(self)
        for i, (k, v) in enumerate(self.options.items()):
            cb = ttk.Checkbutton(win, text=k, variable=v, style="Card.TCheckbutton")
            cb.pack(fill="x", padx=12, pady=6)

        close_btn = ttk.Button(win, text="Close", command=win.destroy, style="Accent.TButton")
        close_btn.pack(pady=8)

    def show_run_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=CARD, fg=FG, activebackground=ACCENT, activeforeground=FG)
        for mode in self.run_modes:
            menu.add_radiobutton(
                label=mode,
                variable=self.run_mode,
                value=mode,
                background=CARD,
                foreground=FG,
                selectcolor=ACCENT
            )
        menu.post(self.winfo_pointerx(), self.winfo_pointery())

    def _on_run_mode_change(self, *_args):
        mode = self.run_mode.get()
        if mode == "run valgrind":
            self.run_btn.config(text="Run with Valgrind")
        else:
            self.run_btn.config(text="Run program")

    def compile_action(self):
        # selected_file_paths: list[str] = []
        #
        #
        # for item_id, checked in self.checked_state.items():
        #     if not checked:
        #         continue
        #     node_type = self.tree.set(item_id, "type")
        #     path = self.tree.set(item_id, "path")
        #     if not path:
        #         continue
        #     if node_type == "file":
        #         selected_file_paths.append(path)
        #     elif node_type == "dir":
        #         selected_file_paths.extend(self._collect_files_under(path))
        #
        # # Deduplicate while preserving order
        # seen: set[str] = set()
        # unique_selected = []
        # for path in selected_file_paths:
        #     if path not in seen:
        #         seen.add(path)
        #         unique_selected.append(path)
        #
        # std = self.cpp_standard.get()
        # opts = {k: v.get() for k, v in self.options.items()}
        # out = self.output_name.get()
        # info = f"Compiling {len(unique_selected)} files\nStandard: {std}\nOptions: {opts}\nOutput: {out}"
        # messagebox.showinfo("Compile", info)
        # print(info)
        #
        # if unique_selected:
        #     normalized = [p.replace("\\", "/") for p in unique_selected]
        #     print("paths:", " ".join(normalized))
        # else:
        #     print("no files selected")
        cpp_files = self._gather_checked_paths()
        root_path = shelling.windows_to_wsl(self.root_directory)
        recording_out = self.root_directory + "\\output.txt"

        distro_name = None  # e.g. "Ubuntu-22.04"
        ok = shelling.compile_in_wsl(cpp_files, distro=distro_name, root_path=root_path,
                                     custom_options=self.options,
                                     language_standard=self.cpp_standard.get(),
                                     executable_name=self.output_name.get())
        if not ok:
            print("Compilation failed; fix errors then re-run.")
            return


    def run_action(self):
        out = self.output_name.get()
        mode = self.run_mode.get()
        
        if mode == "run valgrind":
            cmd = f"cd {shelling.windows_to_wsl(self.root_directory)} && valgrind --leak-check=full ./{out}"
        else:
            cmd = f"cd {shelling.windows_to_wsl(self.root_directory)} && ./{out}"

        print("doing this: ", cmd)

        shelling.run_wsl_command(cmd, distro=None, capture=False, keep_open="pause")


if __name__ == "__main__":
    app = MyApp()
    app.mainloop()

    # from typing import Optional, Union
    # import shutil
    # import subprocess
    #
    #
    # def run_wsl_command(
    #         cmd: str,
    #         distro: Optional[str] = None,
    #         capture: bool = False,
    #         keep_open: Optional[str] = None,  # None | "shell" | "pause"
    # ) -> Union[subprocess.CompletedProcess, subprocess.Popen]:
    #     """
    #     Run a WSL command.
    #
    #     - capture=True: run in-process and return CompletedProcess (stdout/stderr captured).
    #     - capture=False: open a new terminal window running the command.
    #     - keep_open:
    #         - None (default): close when command finishes.
    #         - "shell": after the cmd finishes, start an interactive bash in that window.
    #         - "pause": after the cmd finishes, prompt "Press any key to exit..." and wait.
    #
    #     Notes:
    #     - With the "start" fallback (cmd.exe /c start) the returned Popen usually refers
    #       to the short-lived cmd.exe wrapper. If you need to reliably wait for the
    #       window to close, prefer Windows Terminal (wt.exe) or use keep_open to create
    #       a long-lived process inside the terminal.
    #     """
    #     if keep_open == "shell":
    #         wrapped_cmd = f'{cmd}; echo; exec bash'
    #     elif keep_open == "pause":
    #         wrapped_cmd = f'{cmd}; echo; read -n1 -r -p "Press any key to exit..."'
    #     else:
    #         wrapped_cmd = cmd
    #
    #     # WSL command base
    #     wsl_base = ["wsl.exe"]
    #     if distro:
    #         wsl_base += ["-d", distro]
    #     wsl_base += ["--", "bash", "-lc", wrapped_cmd]
    #
    #     if capture:
    #         # same behavior as before
    #         return subprocess.run(wsl_base, text=True, capture_output=True)
    #
    #     # Non-capture: open a new terminal window
    #     wt_path = shutil.which("wt.exe") or shutil.which("wt")
    #     if wt_path:
    #         # Windows Terminal: spawn wsl; WT usually spawns the window and returns quickly,
    #         # but the shell inside the window will remain if we used keep_open.
    #         wt_args = [wt_path, "wsl"]
    #         if distro:
    #             wt_args += ["-d", distro]
    #         wt_args += ["--", "bash", "-lc", wrapped_cmd]
    #         return subprocess.Popen(wt_args, close_fds=True)
    #
    #     # Fallback: cmd.exe /c start "" wsl.exe ...  (start opens a new window)
    #     start_args = ["cmd.exe", "/c", "start", "", "wsl.exe"]
    #     if distro:
    #         start_args += ["-d", distro]
    #     start_args += ["--", "bash", "-lc", wrapped_cmd]
    #     # Note: Popen here refers to the short-lived cmd.exe process (it returns immediately).
    #     return subprocess.Popen(start_args, shell=False, close_fds=True)

    # run_wsl_command('read -p "Enter your name: " name && echo "Hello $name"', keep_open="pause")
