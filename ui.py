import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import subprocess
import sys
from pathlib import Path
import json
import logging
import threading
import logic
from models import FileNode, FolderNode
from strategies import find_common_strategy, find_duplicates_strategy, utils
from config import config
import file_operations
from project_manager import ProjectManager
from controller import AppController

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ToolTip:
    """
    Create a tooltip for a given widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

class FolderComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title(config.get('ui.title', "Folder Comparison Tool"))
        self.controller = None # Will be set by the controller
        self.build_buttons = []
        self.folder_list_box = None

    def setup_ui(self):
        # --- Tracers ---
        self.app_mode.trace_add('write', self._on_mode_change)
        self.file_type_filter.trace_add('write', self._on_file_type_change)
        self.compare_content_md5.trace_add('write', self._toggle_md5_warning)
        self.compare_histogram.trace_add('write', self._toggle_histogram_options)
        self.histogram_method.trace_add('write', self._update_histogram_threshold_ui)

        self.create_widgets()
        self._set_main_ui_state('disabled')
        use_llm = config.get("use_llm", True)
        if not use_llm:
            if hasattr(self, 'llm_checkbox'):
                self.llm_checkbox.config(state='disabled')
        logger.info("Application initialized.")

    def create_widgets(self):
        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=config.get('ui.labels.new_project', "New Project"), command=lambda: self.controller.project_manager.new_project())
        file_menu.add_command(label=config.get('ui.labels.open_project', "Open Project..."), command=lambda: self.controller.project_manager.load_project())
        file_menu.add_command(label=config.get('ui.labels.save', "Save"), command=lambda: self.controller.project_manager.save_project())
        file_menu.add_command(label=config.get('ui.labels.save_as', "Save Project As..."), command=lambda: self.controller.project_manager.save_project_as())
        file_menu.add_separator()
        file_menu.add_command(label=config.get('ui.labels.exit', "Exit"), command=self.root.quit)
        menubar.add_cascade(label=config.get('ui.labels.file', "File"), menu=file_menu)

        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=config.get('ui.labels.options', "Options"), menu=options_menu)
        mode_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label=config.get('ui.labels.mode', "Mode"), menu=mode_menu)
        mode_menu.add_radiobutton(label=config.get('ui.modes.compare', "Compare Folders"), variable=self.app_mode, value="compare")
        mode_menu.add_radiobutton(label=config.get('ui.modes.duplicates', "Find Duplicates"), variable=self.app_mode, value="duplicates")

        options_menu.add_separator()

        file_type_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label=config.get('ui.labels.file_type', "File Type"), menu=file_type_menu)
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.all', "All"), variable=self.file_type_filter, value="all")
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.image', "Images"), variable=self.file_type_filter, value="image")
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.video', "Videos"), variable=self.file_type_filter, value="video")
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.audio', "Audio"), variable=self.file_type_filter, value="audio")
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.document', "Documents"), variable=self.file_type_filter, value="document")

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=(10,0))

        self.main_content_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)

        self.folder_selection_area = tk.Frame(self.main_content_frame)
        self.folder_selection_area.pack(fill=tk.X)

        # --- Create UI Frames for different modes ---
        self.compare_folders_mode_frame = self._create_compare_folders_frame()
        self.duplicates_mode_frame = self._create_folder_selection_frame(config.get('ui.labels.folder_to_analyze', "Folder to Analyze"))
        options_frame = tk.LabelFrame(self.main_content_frame, text=config.get('ui.labels.options_frame', "Options"), padx=10, pady=10); options_frame.pack(fill=tk.X, pady=10)
        match_frame = tk.LabelFrame(options_frame, text=config.get('ui.labels.match_find_based_on', "Match/Find based on:"), padx=5, pady=5); match_frame.pack(fill=tk.X)

        name_cb = tk.Checkbutton(match_frame, text=config.get('ui.labels.name', "Name"), variable=self.compare_name); name_cb.pack(side=tk.LEFT, padx=5)
        ToolTip(name_cb, "Compare files by their exact file name.")
        date_cb = tk.Checkbutton(match_frame, text=config.get('ui.labels.date', "Date"), variable=self.compare_date); date_cb.pack(side=tk.LEFT, padx=5)
        ToolTip(date_cb, "Compare files by their last modified date.")
        size_cb = tk.Checkbutton(match_frame, text=config.get('ui.labels.size', "Size"), variable=self.compare_size); size_cb.pack(side=tk.LEFT, padx=5)
        ToolTip(size_cb, "Compare files by their exact size in bytes.")
        md5_cb = tk.Checkbutton(match_frame, text=config.get('ui.labels.content_md5', "Content (MD5 Hash)"), variable=self.compare_content_md5); md5_cb.pack(side=tk.LEFT, padx=5)
        ToolTip(md5_cb, "Compare files by their content using MD5 hash. Slower, but very accurate.")

        self.image_match_frame = tk.LabelFrame(options_frame, text=config.get('ui.labels.image_match_options', "Image Match Options"), padx=5, pady=5)
        self.image_match_frame.pack(fill=tk.X, pady=(5,0))

        hist_cb = tk.Checkbutton(self.image_match_frame, text=config.get('ui.labels.content_histogram', "Content (Histogram)"), variable=self.compare_histogram); hist_cb.pack(side=tk.LEFT, padx=5)
        ToolTip(hist_cb, "Compare images by their color histogram. Good for finding similar-looking images.")

        # LLM Frame
        llm_frame = tk.Frame(self.image_match_frame)
        llm_frame.pack(side=tk.LEFT, padx=5)
        self.llm_checkbox = tk.Checkbutton(llm_frame, text=config.get('ui.labels.llm_content', "LLM Content"), variable=self.compare_llm)
        self.llm_checkbox.pack(side=tk.LEFT)
        ToolTip(self.llm_checkbox, "Use a Large Language Model (LLM) to compare image content. Very powerful but requires a capable model.")

        tk.Label(llm_frame, text=config.get('ui.labels.llm_threshold_label', "Threshold:")).pack(side=tk.LEFT, pady=5)
        self.llm_threshold_entry = tk.Entry(llm_frame, textvariable=self.llm_similarity_threshold, width=8)
        self.llm_threshold_entry.pack(side=tk.LEFT, padx=2, pady=5)
        ToolTip(self.llm_threshold_entry, "Similarity threshold for LLM comparison (e.g., 0.85). Higher is stricter.")
        tk.Label(llm_frame, text=config.get('ui.labels.llm_threshold_range', "(0.0-1.0)")).pack(side=tk.LEFT, pady=5)


        self.histogram_options_frame = tk.Frame(self.image_match_frame)

        # Method Selection
        tk.Label(self.histogram_options_frame, text=config.get('ui.labels.histogram_method_label', "Method:")).pack(side=tk.LEFT, pady=5)
        histogram_methods = list(config.get('histogram_methods', {}).keys())
        self.histogram_method_combo = ttk.Combobox(
            self.histogram_options_frame,
            textvariable=self.histogram_method,
            values=histogram_methods,
            state='readonly',
            width=15
        )
        self.histogram_method_combo.pack(side=tk.LEFT, padx=(2, 10), pady=5)
        self.histogram_method_combo.bind("<Key>", lambda e: "break")
        ToolTip(self.histogram_method_combo, "The mathematical method used to compare image histograms.")

        # Threshold Entry
        tk.Label(self.histogram_options_frame, text=config.get('ui.labels.histogram_threshold_label', "Threshold:")).pack(side=tk.LEFT, pady=5)
        self.histogram_threshold_entry = tk.Entry(self.histogram_options_frame, textvariable=self.histogram_threshold, width=8)
        self.histogram_threshold_entry.pack(side=tk.LEFT, padx=2, pady=5)
        ToolTip(self.histogram_threshold_entry, "Similarity threshold for histogram comparison. The required value depends on the method selected.")
        self.histogram_threshold_info_label = tk.Label(self.histogram_options_frame, text="", width=20)
        self.histogram_threshold_info_label.pack(side=tk.LEFT, padx=(0, 5), pady=5)

        self.md5_warning_label = tk.Label(match_frame, text=config.get('ui.labels.md5_warning', "Warning: Content comparison is slow."), fg="red")

        move_to_frame = tk.LabelFrame(options_frame, text=config.get('ui.labels.file_actions', "File Actions"), padx=5, pady=5)
        move_to_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(move_to_frame, text=config.get('ui.labels.move_to_folder', "Move to Folder:")).pack(side=tk.LEFT)
        move_to_entry = tk.Entry(move_to_frame, textvariable=self.move_to_path); move_to_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ToolTip(move_to_entry, "The destination folder for the 'Move' action.")
        browse_btn = tk.Button(move_to_frame, text=config.get('ui.labels.browse', "Browse..."), command=self.select_move_to_folder); browse_btn.pack(side=tk.LEFT)
        ToolTip(browse_btn, "Select a folder to move files to.")
        action_frame = tk.Frame(self.main_content_frame); action_frame.pack(fill=tk.X, pady=5)
        self.action_button = tk.Button(action_frame, text="Compare", command=self.controller.run_action); self.action_button.pack()
        ToolTip(self.action_button, "Run the comparison or duplicate finding process based on the selected options.")
        results_frame = tk.LabelFrame(self.main_content_frame, text=config.get('ui.labels.results_frame', "Results"), padx=10, pady=10); results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.results_tree = ttk.Treeview(results_frame, columns=('File', 'Size', 'Path'), show='headings')
        self.results_tree.heading('File', text=config.get('ui.labels.results_tree_file', 'File Name'))
        self.results_tree.heading('Size', text=config.get('ui.labels.results_tree_size', 'Size (Bytes)'))
        self.results_tree.heading('Path', text=config.get('ui.labels.results_tree_path', 'Relative Path'))
        self.results_tree.column('File', width=250, anchor=tk.W)
        self.results_tree.column('Size', width=100, anchor=tk.E)
        self.results_tree.column('Path', width=400, anchor=tk.W)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(results_frame, command=self.results_tree.yview); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.config(yscrollcommand=scrollbar.set)
        self.results_tree.bind('<Double-1>', self._on_double_click)
        self.results_tree.bind('<Button-3>', self._show_context_menu)
        self.results_tree.bind('<Button-2>', self._show_context_menu)
        self.results_tree.bind('<Control-Button-1>', self._show_context_menu)

        # --- Status Bar ---
        self.status_label = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._on_mode_change()
        self._on_file_type_change()
        self._toggle_histogram_options()
        self._update_histogram_threshold_ui()

        # --- Keyboard Shortcuts ---
        self.root.bind('<Control-b>', self.controller.build_active_folders)
        self.root.bind('<Control-r>', self.controller.run_action)

    def _create_compare_folders_frame(self):
        frame = tk.LabelFrame(self.folder_selection_area, text=config.get('ui.labels.folders_to_compare', "Folders to Compare"), padx=10, pady=10)

        # Base folder selection row
        row = tk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=config.get('ui.labels.base_folder', "Base Folder:")).pack(side=tk.LEFT)
        entry = tk.Entry(row, textvariable=self.base_folder_path); entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ToolTip(entry, "Select the parent folder containing the subdirectories you want to compare.")
        browse_button = tk.Button(row, text=config.get('ui.labels.browse', "Browse..."), command=self.select_base_folder); browse_button.pack(side=tk.LEFT)
        ToolTip(browse_button, "Select a base folder.")
        scan_button = tk.Button(row, text=config.get('ui.labels.scan', "Scan Folders"), command=self.scan_base_folder); scan_button.pack(side=tk.LEFT, padx=(5,0))
        ToolTip(scan_button, "Scan for subdirectories in the base folder.")

        build_button = tk.Button(frame, text=config.get('ui.labels.build', "Build"), command=lambda: self.controller.build_compare_folders())
        build_button.pack(anchor=tk.W, pady=(5,0))
        ToolTip(build_button, "Build metadata for the first two folders in the list. Required before comparing.")
        self.build_buttons.append(build_button)

        # Folder listbox
        list_frame = tk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5,0))
        self.folder_list_box = tk.Listbox(list_frame)
        self.folder_list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, command=self.folder_list_box.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.folder_list_box.config(yscrollcommand=scrollbar.set)
        ToolTip(self.folder_list_box, "The application will compare the first two folders in this list.")

        subfolder_cb = tk.Checkbutton(frame, text=config.get('ui.labels.include_subfolders', "Include subfolders"), variable=self.include_subfolders); subfolder_cb.pack(anchor=tk.W, pady=(5,0))
        ToolTip(subfolder_cb, "If checked, all subdirectories of the selected folder(s) will be included in the analysis.")
        return frame

    def _create_folder_selection_frame(self, frame_text):
        frame = tk.LabelFrame(self.folder_selection_area, text=frame_text, padx=10, pady=10)

        def create_row(parent, label_text, path_var, browse_cmd, build_cmd):
            row = tk.Frame(parent)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label_text).pack(side=tk.LEFT)
            entry = tk.Entry(row, textvariable=path_var); entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            ToolTip(entry, "The full path to the folder.")
            browse_button = tk.Button(row, text=config.get('ui.labels.browse', "Browse..."), command=browse_cmd); browse_button.pack(side=tk.LEFT)
            ToolTip(browse_button, "Select a folder to analyze.")
            build_button = tk.Button(row, text=config.get('ui.labels.build', "Build"), command=build_cmd)
            build_button.pack(side=tk.LEFT, padx=(5, 0))
            ToolTip(build_button, "Scan the selected folder and build the file structure. This is required before running a comparison.")
            self.build_buttons.append(build_button)

        create_row(frame, config.get('ui.labels.folder_1', "Folder 1:"), self.folder1_path, self.select_folder1, lambda: self.controller._build_metadata(1))

        subfolder_cb = tk.Checkbutton(frame, text=config.get('ui.labels.include_subfolders', "Include subfolders"), variable=self.include_subfolders); subfolder_cb.pack(anchor=tk.W, pady=(5,0))
        ToolTip(subfolder_cb, "If checked, all subdirectories of the selected folder(s) will be included in the analysis.")
        return frame

    def _on_mode_change(self, *args):
        mode = self.app_mode.get()
        self.compare_folders_mode_frame.pack_forget()
        self.duplicates_mode_frame.pack_forget()

        if mode == "compare":
            self.compare_folders_mode_frame.pack(fill=tk.X)
            self.action_button.config(text=config.get('ui.modes.compare', "Compare Folders"))
        elif mode == "duplicates":
            self.duplicates_mode_frame.pack(fill=tk.X)
            self.action_button.config(text=config.get('ui.modes.duplicates', "Find Duplicates"))

    def _on_file_type_change(self, *args):
        if self.file_type_filter.get() == "image":
            self.image_match_frame.pack(fill=tk.X, pady=(5,0))
        else:
            self.image_match_frame.pack_forget()
            # Also uncheck the options when they are hidden
            self.compare_histogram.set(False)
            self.compare_llm.set(False)

    def _set_main_ui_state(self, state='normal'):
        def set_state_recursive(widget):
            if widget.winfo_class() == 'Menu': return
            try: widget.config(state=state)
            except tk.TclError: pass
            for child in widget.winfo_children(): set_state_recursive(child)
        set_state_recursive(self.main_content_frame)


    def update_status(self, message, progress_value=None):
        self.status_label.config(text=message)
        if progress_value is not None:
            self.progress_bar['value'] = progress_value
        self.root.update_idletasks()

    def select_folder1(self):
        path = filedialog.askdirectory()
        if path:
            self.folder1_path.set(path)
            logger.info(f"Selected folder 1: {path}")

    def select_folder2(self):
        path = filedialog.askdirectory()
        if path:
            self.folder2_path.set(path)
            logger.info(f"Selected folder 2: {path}")

    def select_move_to_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.move_to_path.set(path)
            logger.info(f"Selected move-to folder: {path}")

    def select_base_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.base_folder_path.set(path)
            logger.info(f"Selected base folder: {path}")
            self.scan_base_folder()

    def scan_base_folder(self):
        self.controller.scan_base_folder()

    def _on_double_click(self, event):
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        # Try to get the relative path from column 2, otherwise fall back to column 0
        text_to_copy = ""
        if item['values'] and len(item['values']) > 2 and item['values'][2]:
            text_to_copy = item['values'][2].strip()
        elif item['values']:
            text_to_copy = item['values'][0].strip()

        # Avoid copying headers or info messages
        if text_to_copy and "Duplicate Set" not in text_to_copy and "No " not in text_to_copy:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(text_to_copy)
                self.status_label.config(text=f"Copied to clipboard: {text_to_copy}")
            except tk.TclError:
                self.status_label.config(text="Error: Could not copy to clipboard.")
    def _toggle_md5_warning(self, *args):
        if self.compare_content_md5.get(): self.md5_warning_label.pack(side=tk.LEFT, padx=20)
        else: self.md5_warning_label.pack_forget()

    def _toggle_histogram_options(self, *args):
        if self.compare_histogram.get():
            self.histogram_options_frame.pack(fill=tk.X, pady=5)
        else:
            self.histogram_options_frame.pack_forget()

    def _update_histogram_threshold_ui(self, *args):
        method = self.histogram_method.get()
        if not method:
            return

        # Get the defaults from config
        method_settings = config.get(f'histogram_methods.{method}')
        if not method_settings:
            self.histogram_threshold_info_label.config(text="")
            self.histogram_threshold.set("")
            return

        info_text = method_settings.get('info_text', '')
        default_threshold = str(method_settings.get('default_threshold', ''))

        self.histogram_threshold_info_label.config(text=info_text)
        # Only set the default if the variable is not already set to something else
        if not self.histogram_threshold.get():
             self.histogram_threshold.set(default_threshold)

    def _get_selected_file_info(self, folder_num):
        """Gets the iid, relative path, and base path for the selected file."""
        iid, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return None, None, None

        # In duplicates mode, folder_num is always 1, but the UI might show folder 2 path if it was switched from compare mode.
        # We should use the path that is actually being displayed.
        mode = self.app_mode.get()
        if mode == 'duplicates':
            base_path_str = self.folder1_path.get()
        else: # compare mode
            base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()

        if not base_path_str:
            logger.warning(f"Action cancelled: folder {folder_num} path is not set.")
            messagebox.showwarning("Warning", f"Folder {folder_num} path is not set.")
            return None, None, None
        return iid, relative_path_str, base_path_str

    def _move_file(self, folder_num):
        iid, relative_path, base_path = self._get_selected_file_info(folder_num)
        if not iid:
            return
        dest_path = self.move_to_path.get()
        file_operations.move_file(self.controller, base_path, relative_path, dest_path, self.results_tree, iid, self.update_status)

    def _delete_file(self, folder_num):
        iid, relative_path, base_path = self._get_selected_file_info(folder_num)
        if not iid:
            return
        file_operations.delete_file(self.controller, base_path, relative_path, self.results_tree, iid, self.update_status)

    def _open_containing_folder(self, folder_num):
        _, relative_path, base_path = self._get_selected_file_info(folder_num)
        if not relative_path:
            return
        file_operations.open_containing_folder(base_path, relative_path)

    def _show_context_menu(self, event):
        iid = self.results_tree.identify_row(event.y)
        if not iid:
            return

        self.results_tree.selection_set(iid)
        item = self.results_tree.item(iid)
        if 'file_row' not in item.get('tags', []):
            return

        context_menu = tk.Menu(self.root, tearoff=0)
        _, relative_path_str = self._get_relative_path_from_selection()

        preview_state = tk.DISABLED
        if relative_path_str:
            file_ext = Path(relative_path_str).suffix.lower()
            is_image = file_ext in config.get("file_extensions.image", []) and PIL_AVAILABLE
            is_media = file_ext in config.get("file_extensions.video", []) or file_ext in config.get("file_extensions.audio", [])
            if is_image or is_media:
                preview_state = tk.NORMAL

        move_state = tk.NORMAL if self.move_to_path.get() else tk.DISABLED
        mode = self.app_mode.get()

        menu_items = []
        if mode == "compare":
            menu_items = [
                ('preview_from_folder_1', lambda: self._preview_file(1), preview_state),
                ('preview_from_folder_2', lambda: self._preview_file(2), preview_state),
                'separator',
                ('open_in_folder_1', lambda: self._open_containing_folder(1)),
                ('open_in_folder_2', lambda: self._open_containing_folder(2)),
                'separator',
                ('move_from_folder_1', lambda: self._move_file(1), move_state),
                ('move_from_folder_2', lambda: self._move_file(2), move_state),
                'separator',
                ('delete_from_folder_1', lambda: self._delete_file(1)),
                ('delete_from_folder_2', lambda: self._delete_file(2)),
            ]
        else:  # duplicates mode
            menu_items = [
                ('preview_file', lambda: self._preview_file(1), preview_state),
                'separator',
                ('open_containing_folder', lambda: self._open_containing_folder(1)),
                'separator',
                ('move_file', lambda: self._move_file(1), move_state),
                'separator',
                ('delete_file', lambda: self._delete_file(1)),
            ]

        for item in menu_items:
            if item == 'separator':
                context_menu.add_separator()
            else:
                label_key, command, *state = item
                state = state[0] if state else tk.NORMAL
                default_text = label_key.replace('_', ' ').title()
                label_text = config.get(f'ui.labels.context_menu.{label_key}', default_text)
                context_menu.add_command(label=label_text, command=command, state=state)

        context_menu.post(event.x_root, event.y_root)

    def _get_relative_path_from_selection(self):
        selection = self.results_tree.selection()
        if not selection:
            return None, None

        iid = selection[0]
        item = self.results_tree.item(iid)

        # Perform robust checks to ensure it's a valid file row with a path
        is_file_row = 'file_row' in item.get('tags', [])
        has_values = item.get('values')
        has_path = has_values and len(has_values) > 2 and has_values[2]

        if is_file_row and has_path:
            return iid, has_values[2].strip()

        return None, None

    def _preview_file(self, folder_num):
        _, relative_path, base_path = self._get_selected_file_info(folder_num)
        if not relative_path:
            return

        full_path = Path(base_path) / relative_path
        logger.info(f"Attempting to preview file: {full_path}")
        if not full_path.is_file():
            logger.error(f"Preview failed: file does not exist at '{full_path}'.")
            messagebox.showerror("Error", f"File does not exist:\n{full_path}")
            return

        file_ext = full_path.suffix.lower()
        try:
            if file_ext in config.get("file_extensions.image", []) and PIL_AVAILABLE:
                logger.debug(f"Displaying image preview for: {full_path}")
                win = tk.Toplevel(self.root)
                win.title(full_path.name)
                img = Image.open(full_path)
                img.thumbnail((800, 600)) # Resize for display
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(win, image=photo)
                label.image = photo # Keep a reference!
                label.pack()
            elif file_ext in config.get("file_extensions.video", []) or file_ext in config.get("file_extensions.audio", []):
                logger.debug(f"Opening media file with default player: {full_path}")
                if sys.platform == "win32":
                    os.startfile(full_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(full_path)])
                else:
                    subprocess.Popen(["xdg-open", str(full_path)])
        except Exception as e:
            logger.error(f"Failed to preview file: {full_path}", exc_info=True)
            messagebox.showerror("Error", f"Could not preview file:\n{e}")



    def _update_filenode_metadata(self, structure, metadata_info, base_path):
        """Recursively update metadata of FileNodes in the structure."""
        base_path_obj = Path(base_path)
        for node in structure:
            if isinstance(node, FileNode):
                try:
                    relative_path = Path(node.fullpath).relative_to(base_path_obj)
                    if relative_path in metadata_info:
                        # Only update with the 'metadata' part of the info dict
                        if 'metadata' in metadata_info[relative_path]:
                            node.metadata.update(metadata_info[relative_path]['metadata'])
                except ValueError:
                    continue
            elif isinstance(node, FolderNode):
                self._update_filenode_metadata(node.content, metadata_info, base_path)
