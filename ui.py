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

class FolderComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Comparison Tool")
        self.controller = None # Will be set by the controller
        self.build_buttons = []

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
        file_menu.add_command(label="New Project", command=lambda: self.controller.project_manager.new_project())
        file_menu.add_command(label="Open Project...", command=lambda: self.controller.project_manager.load_project())
        file_menu.add_command(label="Save", command=lambda: self.controller.project_manager.save_project())
        file_menu.add_command(label="Save Project As...", command=lambda: self.controller.project_manager.save_project_as())
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        mode_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="Mode", menu=mode_menu)
        mode_menu.add_radiobutton(label="Compare Folders", variable=self.app_mode, value="compare")
        mode_menu.add_radiobutton(label="Find Duplicates", variable=self.app_mode, value="duplicates")
        mode_menu.add_radiobutton(label="Folder Search", variable=self.app_mode, value="search")

        options_menu.add_separator()

        file_type_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="File Type", menu=file_type_menu)
        file_type_menu.add_radiobutton(label="All", variable=self.file_type_filter, value="all")
        file_type_menu.add_radiobutton(label="Images", variable=self.file_type_filter, value="image")
        file_type_menu.add_radiobutton(label="Videos", variable=self.file_type_filter, value="video")
        file_type_menu.add_radiobutton(label="Audio", variable=self.file_type_filter, value="audio")
        file_type_menu.add_radiobutton(label="Documents", variable=self.file_type_filter, value="document")

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=(10,0))

        self.main_content_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)

        self.folder_selection_area = tk.Frame(self.main_content_frame)
        self.folder_selection_area.pack(fill=tk.X)

        # --- Create UI Frames for different modes ---
        self.compare_mode_frame = self._create_folder_selection_frame("Folders to Compare", two_folders=True)
        self.duplicates_mode_frame = self._create_folder_selection_frame("Folder to Analyze")
        self.search_mode_frame = self._create_folder_selection_frame("Folder to Search")

        search_options_frame = tk.LabelFrame(self.search_mode_frame, text="Search Criteria", padx=10, pady=10)
        search_options_frame.pack(fill=tk.X, pady=10)
        tk.Label(search_options_frame, text="Size is greater than (MB):").pack(side=tk.LEFT, pady=5)
        tk.Entry(search_options_frame, textvariable=self.search_size_greater_than, width=8).pack(side=tk.LEFT, padx=2, pady=5)
        options_frame = tk.LabelFrame(self.main_content_frame, text="Options", padx=10, pady=10); options_frame.pack(fill=tk.X, pady=10)
        match_frame = tk.LabelFrame(options_frame, text="Match/Find based on:", padx=5, pady=5); match_frame.pack(fill=tk.X)
        tk.Checkbutton(match_frame, text="Name", variable=self.compare_name).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(match_frame, text="Date", variable=self.compare_date).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(match_frame, text="Size", variable=self.compare_size).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(match_frame, text="Content (MD5 Hash)", variable=self.compare_content_md5).pack(side=tk.LEFT, padx=5)

        self.image_match_frame = tk.LabelFrame(options_frame, text="Image Match Options", padx=5, pady=5)
        self.image_match_frame.pack(fill=tk.X, pady=(5,0))

        tk.Checkbutton(self.image_match_frame, text="Content (Histogram)", variable=self.compare_histogram).pack(side=tk.LEFT, padx=5)
        self.llm_checkbox = tk.Checkbutton(self.image_match_frame, text="LLM Content", variable=self.compare_llm, command=self._toggle_llm_options)
        self.llm_checkbox.pack(side=tk.LEFT, padx=5)

        self.llm_options_frame = tk.Frame(self.image_match_frame)
        tk.Label(self.llm_options_frame, text="Similarity:").pack(side=tk.LEFT, pady=5)
        tk.Entry(self.llm_options_frame, textvariable=self.llm_similarity_threshold, width=8).pack(side=tk.LEFT, padx=2, pady=5)
        tk.Label(self.llm_options_frame, text="(Higher is more similar)").pack(side=tk.LEFT, padx=(0, 5), pady=5)

        self.histogram_options_frame = tk.Frame(self.image_match_frame)

        # Method Selection
        tk.Label(self.histogram_options_frame, text="Method:").pack(side=tk.LEFT, pady=5)
        self.histogram_method_combo = ttk.Combobox(
            self.histogram_options_frame,
            textvariable=self.histogram_method,
            values=['Correlation', 'Chi-Square', 'Intersection', 'Bhattacharyya'],
            state='readonly',
            width=15
        )
        self.histogram_method_combo.pack(side=tk.LEFT, padx=(2, 10), pady=5)
        self.histogram_method_combo.bind("<Key>", lambda e: "break")

        # Threshold Entry
        tk.Label(self.histogram_options_frame, text="Threshold:").pack(side=tk.LEFT, pady=5)
        self.histogram_threshold_entry = tk.Entry(self.histogram_options_frame, textvariable=self.histogram_threshold, width=8)
        self.histogram_threshold_entry.pack(side=tk.LEFT, padx=2, pady=5)
        self.histogram_threshold_info_label = tk.Label(self.histogram_options_frame, text="", width=20)
        self.histogram_threshold_info_label.pack(side=tk.LEFT, padx=(0, 5), pady=5)

        self.md5_warning_label = tk.Label(match_frame, text="Warning: Content comparison is slow.", fg="red")

        move_to_frame = tk.LabelFrame(options_frame, text="File Actions", padx=5, pady=5)
        move_to_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(move_to_frame, text="Move to Folder:").pack(side=tk.LEFT)
        tk.Entry(move_to_frame, textvariable=self.move_to_path).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(move_to_frame, text="Browse...", command=self.select_move_to_folder).pack(side=tk.LEFT)
        action_frame = tk.Frame(self.main_content_frame); action_frame.pack(fill=tk.X, pady=5)
        self.action_button = tk.Button(action_frame, text="Compare", command=self.controller.run_action); self.action_button.pack()
        results_frame = tk.LabelFrame(self.main_content_frame, text="Results", padx=10, pady=10); results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.results_tree = ttk.Treeview(results_frame, columns=('File', 'Size', 'Path'), show='headings')
        self.results_tree.heading('File', text='File Name')
        self.results_tree.heading('Size', text='Size (Bytes)')
        self.results_tree.heading('Path', text='Relative Path')
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
        self._toggle_llm_options()
        self._update_histogram_threshold_ui()

    def _create_folder_selection_frame(self, frame_text, two_folders=False):
        frame = tk.LabelFrame(self.folder_selection_area, text=frame_text, padx=10, pady=10)

        def create_row(parent, label_text, path_var, browse_cmd, build_cmd):
            row = tk.Frame(parent)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label_text).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=path_var).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            tk.Button(row, text="Browse...", command=browse_cmd).pack(side=tk.LEFT)
            build_button = tk.Button(row, text="Build", command=build_cmd)
            build_button.pack(side=tk.LEFT, padx=(5, 0))
            self.build_buttons.append(build_button)

        create_row(frame, "Folder 1:", self.folder1_path, self.select_folder1, lambda: self.controller._build_metadata(1))
        if two_folders:
            create_row(frame, "Folder 2:", self.folder2_path, self.select_folder2, lambda: self.controller._build_metadata(2))

        tk.Checkbutton(frame, text="Include subfolders", variable=self.include_subfolders).pack(anchor=tk.W, pady=(5,0))
        return frame

    def _on_mode_change(self, *args):
        mode = self.app_mode.get()
        self.compare_mode_frame.pack_forget()
        self.duplicates_mode_frame.pack_forget()
        self.search_mode_frame.pack_forget()

        if mode == "compare":
            self.compare_mode_frame.pack(fill=tk.X)
            self.action_button.config(text="Compare")
        elif mode == "duplicates":
            self.duplicates_mode_frame.pack(fill=tk.X)
            self.action_button.config(text="Find Duplicates")
        elif mode == "search":
            self.search_mode_frame.pack(fill=tk.X)
            self.action_button.config(text="Search")

    def _on_file_type_change(self, *args):
        if self.file_type_filter.get() == "image":
            self.image_match_frame.pack(fill=tk.X, pady=(5,0))
        else:
            self.image_match_frame.pack_forget()
            # Also uncheck the options when they are hidden
            self.compare_histogram.set(False)
            self.compare_llm.set(False)
        self._toggle_llm_options()

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

    def _toggle_llm_options(self, *args):
        if self.compare_llm.get():
            self.llm_options_frame.pack(fill=tk.X, pady=5)
        else:
            self.llm_options_frame.pack_forget()

    def _update_histogram_threshold_ui(self, *args):
        method = self.histogram_method.get()
        info_text = ""
        default_threshold = ""

        if method == 'Correlation' or method == 'Intersection':
            info_text = "(Higher value is more similar)"
            default_threshold = "0.9"
        elif method == 'Chi-Square' or method == 'Bhattacharyya':
            info_text = "(Lower value is more similar)"
            default_threshold = "0.1"

        self.histogram_threshold_info_label.config(text=info_text)
        self.histogram_threshold.set(default_threshold)



    

    def _move_file(self, folder_num):
        iid, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return
        base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()
        dest_path_str = self.move_to_path.get()
        file_operations.move_file(base_path_str, relative_path_str, dest_path_str, self.results_tree, iid, self.update_status)

    def _delete_file(self, folder_num):
        iid, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return
        base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()
        file_operations.delete_file(base_path_str, relative_path_str, self.results_tree, iid, self.update_status)

    def _open_containing_folder(self, folder_num):
        _, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return
        base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()
        file_operations.open_containing_folder(base_path_str, relative_path_str)

    def _show_context_menu(self, event):
        iid = self.results_tree.identify_row(event.y)
        if not iid:
            return

        self.results_tree.selection_set(iid)
        item = self.results_tree.item(iid)
        tags = item.get('tags', [])

        # Only show context menu for actual file rows
        if 'file_row' not in tags:
            return

        context_menu = tk.Menu(self.root, tearoff=0)
        _, relative_path_str = self._get_relative_path_from_selection()

        # Determine preview state
        preview_state = tk.DISABLED
        if relative_path_str:
            file_ext = Path(relative_path_str).suffix.lower()
            is_image = file_ext in config.get("file_extensions.image", []) and PIL_AVAILABLE
            is_media = file_ext in config.get("file_extensions.video", []) or file_ext in config.get("file_extensions.audio", [])
            if is_image or is_media:
                preview_state = tk.NORMAL

        # Determine move state
        move_state = tk.NORMAL if self.move_to_path.get() else tk.DISABLED

        # Build menu based on mode
        mode = self.app_mode.get()
        if mode == "compare":
            context_menu.add_command(label="Preview from Folder 1", command=lambda: self._preview_file(1), state=preview_state)
            context_menu.add_command(label="Preview from Folder 2", command=lambda: self._preview_file(2), state=preview_state)
            context_menu.add_separator()
            context_menu.add_command(label="Open in Folder 1", command=lambda: self._open_containing_folder(1))
            context_menu.add_command(label="Open in Folder 2", command=lambda: self._open_containing_folder(2))
            context_menu.add_separator()
            context_menu.add_command(label="Move from Folder 1...", command=lambda: self._move_file(1), state=move_state)
            context_menu.add_command(label="Move from Folder 2...", command=lambda: self._move_file(2), state=move_state)
            context_menu.add_separator()
            context_menu.add_command(label="Delete from Folder 1", command=lambda: self._delete_file(1))
            context_menu.add_command(label="Delete from Folder 2", command=lambda: self._delete_file(2))
        else:  # duplicates mode
            context_menu.add_command(label="Preview File", command=lambda: self._preview_file(1), state=preview_state)
            context_menu.add_separator()
            context_menu.add_command(label="Open Containing Folder", command=lambda: self._open_containing_folder(1))
            context_menu.add_separator()
            context_menu.add_command(label="Move File...", command=lambda: self._move_file(1), state=move_state)
            context_menu.add_separator()
            context_menu.add_command(label="Delete File", command=lambda: self._delete_file(1))

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
        _, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return

        base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()
        if not base_path_str:
            logger.warning(f"Preview cancelled: folder {folder_num} path is not set.")
            messagebox.showwarning("Warning", f"Folder {folder_num} path is not set.")
            return

        full_path = Path(base_path_str) / relative_path_str
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
