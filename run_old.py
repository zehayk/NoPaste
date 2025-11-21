import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import cast

# Folder/file icons (using Unicode symbols)
FOLDER_ICON = "📁"
FOLDER_OPEN_ICON = "📂"
FILE_ICON = "📄"

# Colors
BG = "#07050b"  # very dark with slight purple tint
ACCENT = "#4b1168"  # dark purple accent
CARD = "#0f0813"  # slightly lighter card background
FG = "#e9e6f1"  # light foreground

FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 10, "bold")


class ScrollableFrame(ttk.Frame):
    """A scrollable frame for the file tree area."""

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        # use a canvas + styled ttk scrollbar
        self.canvas = tk.Canvas(self, background=CARD, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
        self.scrollable_frame = ttk.Frame(self.canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class MyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("edgy python gui")
        self.configure(bg=BG)
        self.geometry("900x560")
        self.minsize(820, 480)

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

        # Labels
        style.configure("TLabel", background=BG, foreground=FG, font=FONT_LABEL)
        style.configure("Card.TLabel", background=CARD, foreground=FG, font=FONT_LABEL)

        # Top title bar
        title_bar = ttk.Frame(self, style="Card.TFrame")
        title_bar.pack(fill="x", padx=10, pady=10)
        title_label = ttk.Label(title_bar, text="NoPaste", font=("Segoe UI", 14, "bold"), background=CARD, foreground=FG)
        title_label.pack(side="left", padx=8, pady=6)

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

        self.scrollable = ScrollableFrame(self.file_tree_card)
        self.scrollable.pack(fill="both", expand=True)

        self.file_tree_obj = None
        self.check_vars = {}  # path -> tk.BooleanVar
        self.folder_states = {}  # path -> tk.BooleanVar (True=expanded, False=collapsed)
        self.folder_widgets = {}  # path -> list of widgets to show/hide
        self.tree_row = 0

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
        standards = ["c++98", "c++11", "c++14", "c++17", "c++20", "c++23"]
        self.std_combo = ttk.Combobox(options_row, values=standards, textvariable=self.cpp_standard, state="readonly",
                                      width=12)
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
        run_btn = ttk.Button(action_frame, text="Run program", command=self.run_action, style="Card.TButton")
        run_btn.pack(side="left")

        # state for options popup
        self.options = {
            "Optimize": tk.BooleanVar(value=False),
            "Debug info": tk.BooleanVar(value=False),
            "Warnings as errors": tk.BooleanVar(value=False),
            "Link static": tk.BooleanVar(value=False),
        }

    def select_directory(self):
        folder = filedialog.askdirectory()
        print("selected directory: ", folder)
        if folder:
            self.populate_file_tree(folder)

    def clear_file_tree(self):
        for child in self.scrollable.scrollable_frame.winfo_children():
            child.destroy()
        self.check_vars.clear()
        self.folder_states.clear()
        self.folder_widgets.clear()
        self.tree_row = 0

    def toggle_folder(self, subfolder: 'Folder'):
        """Toggle folder expand/collapse state"""
        # is_expanded = self.folder_states.get(folder_path, tk.BooleanVar(value=True))
        # is_expanded.set(not is_expanded.get())
        newState = not subfolder.is_collapsed
        subfolder.is_collapsed = newState

        def rec(sub):
            def a(f):
                if newState:
                    f.widget.grid()
                else:
                    f.widget.grid_remove()

            for i in sub.folders:
                a(i)
                rec(i)
            for i in sub.files:
                a(i)

        rec(subfolder)

    def populate_file_tree(self, root_dir: str, depth=0, max_depth=3):
        self.clear_file_tree()

        file_tree = Folder.build_from_path(root_dir)
        self.file_tree_obj = file_tree

        def build_single_row(node: Node, depth=0):
            indent = "  " * depth

            if type(node) == Folder:
                node = cast(Folder, node)
                var = tk.BooleanVar(value=False)
                node.is_selected = var

                # Create folder row with expand/collapse button and icon
                folder_frame = ttk.Frame(self.scrollable.scrollable_frame, style="Card.TFrame")
                folder_frame.grid(row=self.tree_row, column=0, sticky="ew", padx=6, pady=1)
                node.widget = folder_frame

                # Folder checkbox
                cb = ttk.Checkbutton(folder_frame, variable=var, style="Card.TCheckbutton")
                cb.pack(side="left", padx=(len(indent) * 8, 4))

                # Create toggle button (▼ when expanded, ▶ when collapsed)
                toggle_btn = tk.Label(folder_frame, text="▼", bg=CARD, fg=FG, cursor="hand2", font=("Segoe UI", 8))
                toggle_btn.pack(side="left")

                # Folder icon and name
                folder_label = tk.Label(folder_frame, text=f"{FOLDER_ICON} {node.name}",
                                        bg=CARD, fg=FG, cursor="hand2", font=FONT_LABEL, anchor="w")
                folder_label.pack(side="left", fill="x", expand=True)

                # Add hover effect
                def on_enter(e, lbl=folder_label):
                    lbl.config(fg="white")

                def on_leave(e, lbl=folder_label):
                    lbl.config(fg=FG)

                folder_label.bind("<Enter>", on_enter)
                folder_label.bind("<Leave>", on_leave)

                # Bind click to toggle
                def make_toggle_handler(btn, subfolder: Folder):
                    def handler(e):
                        self.toggle_folder(subfolder)
                        # Update button icon
                        is_expanded = subfolder.is_collapsed
                        btn.config(text="▼" if is_expanded else "▶")

                    return handler

                toggle_handler = make_toggle_handler(toggle_btn, node)
                toggle_btn.bind("<Button-1>", toggle_handler)
                folder_label.bind("<Button-1>", toggle_handler)

                self.tree_row += 1

            else:
                # Add file with checkbox
                var = tk.BooleanVar(value=False)
                node.is_selected = var

                # Create file row
                file_frame = ttk.Frame(self.scrollable.scrollable_frame, style="Card.TFrame")
                file_frame.grid(row=self.tree_row, column=0, sticky="ew", padx=(6 + (depth + 1) * 16, 6), pady=1)
                node.widget = file_frame

                # Checkbox
                cb = ttk.Checkbutton(file_frame, variable=var, style="Card.TCheckbutton")
                cb.pack(side="left", padx=(0, 4))

                # File icon and name
                file_label = tk.Label(file_frame, text=f"{FILE_ICON} {node.name}",
                                      bg=CARD, fg=FG, cursor="hand2", font=FONT_LABEL, anchor="w")
                file_label.pack(side="left", fill="x", expand=True)

                # Add hover effect
                def on_enter_file(e, lbl=file_label):
                    lbl.config(fg="white")

                def on_leave_file(e, lbl=file_label):
                    lbl.config(fg=FG)

                file_label.bind("<Enter>", on_enter_file)
                file_label.bind("<Leave>", on_leave_file)

                # Click on label toggles checkbox
                def make_click_handler(v):
                    def handler(e):
                        v.set(not v.get())

                    return handler

                file_label.bind("<Button-1>", make_click_handler(var))

                self.tree_row += 1

        def build_file_tree(folder: 'Folder', level=1):
            for sub in folder.folders:
                # print("|" * level, i.name)
                build_single_row(sub, level)
                build_file_tree(sub, level + 1)
            for k in folder.files:
                # print("|" * level, k.name)
                build_single_row(k, level)

        build_single_row(file_tree, 0)
        build_file_tree(file_tree)

    def open_options_popup(self):
        win = tk.Toplevel(self)
        win.title("Options")
        win.configure(bg=BG)
        win.geometry("260x200")
        win.transient(self)
        for i, (k, v) in enumerate(self.options.items()):
            cb = ttk.Checkbutton(win, text=k, variable=v, style="Card.TCheckbutton")
            cb.pack(fill="x", padx=12, pady=6)

        close_btn = ttk.Button(win, text="Close", command=win.destroy, style="Accent.TButton")
        close_btn.pack(pady=8)

    def compile_action(self):
        selected = [p for p, v in self.check_vars.items() if v.get()]
        std = self.cpp_standard.get()
        opts = {k: v.get() for k, v in self.options.items()}
        out = self.output_name.get()
        info = f"Compiling {len(selected)} files\nStandard: {std}\nOptions: {opts}\nOutput: {out}"
        messagebox.showinfo("Compile", info)
        print(info)

        if self.file_tree_obj is not None:
            # print("AAA: ", Folder.print_tree(self.file_tree_obj))
            files_to_compile = Folder.get_selected_files_paths(self.file_tree_obj).replace("\\", "/")
            print("paths: ", files_to_compile)
        else:
            print("files not selected")

    def run_action(self):
        out = self.output_name.get()
        messagebox.showinfo("Run", f"Running {out} (this is a placeholder)")


class Node:
    def __init__(self, name, is_root=False, path=None):
        self.name = name
        self.is_root = is_root
        self.is_selected = False
        self.path = path
        self.widget = None

    @staticmethod
    def is_file_valid(name: str):
        accepted = (".cpp", ".cc", ".cxx", ".c++", ".C", ".CPP",
                    ".c", ".h", ".hpp", ".hh", ".hxx", ".H", ".ii", ".i",
                    ".s", ".S", ".o", ".obj", ".a", ".so", ".dll", ".lib")
        return name.endswith(accepted)


class File(Node):
    def __init__(self, name, path):
        super().__init__(name, path=path)


class Folder(Node):
    def __init__(self, name, is_root=False, path=None):
        super().__init__(name, is_root=is_root, path=path)
        self.folders = []
        self.files = []

        self.is_collapsed = False

    def add_folder(self, folder: 'Folder'):
        self.folders.append(folder)

    def add_file(self, file: File):
        self.files.append(file)

    @staticmethod
    def build_from_path(path) -> 'Folder':
        """
        Expects absolute path to a folder
        :param path:
        :return:
        """
        file_tree = Folder(path.split("\\")[-1], path=path + "\\")

        for item in os.scandir(path):
            if item.is_dir():
                file_tree.add_folder(Folder.build_from_path(item.path))
            else:
                # if Node.is_file_valid(item.name):
                file_tree.add_file(File(item.name, item.path))

        return file_tree

    @staticmethod
    def print_tree(folder: 'Folder', level=1):
        for i in folder.folders:
            print(i.is_selected, "|" * level, i.name)
            Folder.print_tree(i, level + 1)
        for k in folder.files:
            print(k.is_selected, "|" * level, k.name)

    @staticmethod
    def get_selected_files_paths(folder: 'Folder'):
        pathstr = ""

        for i in folder.folders:
            if i.is_selected.get():
                pathstr += f" {i.path}* "
            else:
                pathstr += Folder.get_selected_files_paths(i)
        for k in folder.files:
            if k.is_selected.get():
                pathstr += f" {k.path} "

        return pathstr


if __name__ == "__main__":
    app = MyApp()
    app.mainloop()

    # =====================

    # # path = "C:\\Users\\haykm\\Documents\\school\\cpp course\\NoPaste\\Test Folder"
    # # path = "C:\\Users\\haykm\\Documents\\school\\cpp course\\warzone"
    # path = "C:\\Users\\hayk\\source\\ai_models\\XTTS-v2"
    #
    # # file_tree = Folder("XTTS-v2", is_root=True, path=path)
    #
    #
    # def print_tree(folder: Folder, level=1):
    #     for i in folder.folders:
    #         print("|" * level, i.name, i.path)
    #         print_tree(i, level + 1)
    #     for k in folder.files:
    #         print("|" * level, k.name, k.path)
    #     # print("---------")
    #
    #
    # bigboy = Folder.build_from_path(path)
    # # # print(bigboy)
    # print_tree(bigboy)

    # =====================

    # import subprocess
    #
    # # Run a simple WSL command
    # result = subprocess.run(
    #     ["wsl", "ls", "-la", "/home"],
    #     capture_output=True,
    #     text=True
    # )
    #
    # print(result.stdout)


