import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import subprocess
import sys
import shutil
from pathlib import Path
import json
import logic
from models import FileNode, FolderNode
from strategies import find_common_strategy, find_duplicates_strategy, utils

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']

class FolderComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Comparison Tool")
        self.current_project_path = None
        self.folder1_structure = None
        self.folder2_structure = None

        # --- UI variables ---
        self.folder1_path = tk.StringVar()
        self.folder2_path = tk.StringVar()
        self.app_mode = tk.StringVar(value="compare")
        self.move_to_path = tk.StringVar()

        # --- Comparison options ---
        self.include_subfolders = tk.BooleanVar()
        self.compare_name = tk.BooleanVar(value=True)
        self.compare_date = tk.BooleanVar()
        self.compare_size = tk.BooleanVar()
        self.compare_content_md5 = tk.BooleanVar()
        self.compare_histogram = tk.BooleanVar()
        self.histogram_method = tk.StringVar(value='Correlation')
        self.histogram_threshold = tk.StringVar(value='0.9')

        # --- Tracers ---
        self.app_mode.trace_add('write', self._on_mode_change)
        self.compare_content_md5.trace_add('write', self._toggle_md5_warning)
        self.compare_histogram.trace_add('write', self._toggle_histogram_options)
        self.histogram_method.trace_add('write', self._update_histogram_threshold_ui)

        self.create_widgets()
        self._set_main_ui_state('disabled')

    def create_widgets(self):
        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Project", command=self._new_project)
        file_menu.add_command(label="Open Project...", command=self._load_project)
        file_menu.add_command(label="Save", command=self._save_project)
        file_menu.add_command(label="Save Project As...", command=self._save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=(10,0))

        mode_frame = tk.LabelFrame(top_frame, text="Mode", padx=10, pady=5)
        mode_frame.pack(fill=tk.X)
        tk.Radiobutton(mode_frame, text="Compare Folders", variable=self.app_mode, value="compare").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="Find Duplicates", variable=self.app_mode, value="duplicates").pack(side=tk.LEFT, padx=10)

        self.main_content_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)

        self.folder_selection_area = tk.Frame(self.main_content_frame)
        self.folder_selection_area.pack(fill=tk.X)

        # --- Compare Mode UI ---
        self.compare_mode_frame = tk.LabelFrame(self.folder_selection_area, text="Folders to Compare", padx=10, pady=10)
        row1 = tk.Frame(self.compare_mode_frame); row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Folder 1:").pack(side=tk.LEFT); tk.Entry(row1, textvariable=self.folder1_path).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(row1, text="Browse...", command=self.select_folder1).pack(side=tk.LEFT)
        self.build_button_compare1 = tk.Button(row1, text="Build", command=lambda: self._build_metadata(1)); self.build_button_compare1.pack(side=tk.LEFT, padx=(5,0))
        row2 = tk.Frame(self.compare_mode_frame); row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Folder 2:").pack(side=tk.LEFT); tk.Entry(row2, textvariable=self.folder2_path).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(row2, text="Browse...", command=self.select_folder2).pack(side=tk.LEFT)
        self.build_button_compare2 = tk.Button(row2, text="Build", command=lambda: self._build_metadata(2)); self.build_button_compare2.pack(side=tk.LEFT, padx=(5,0))

        # --- Duplicates Mode UI ---
        self.duplicates_mode_frame = tk.LabelFrame(self.folder_selection_area, text="Folder to Analyze", padx=10, pady=10)
        dupes_row = tk.Frame(self.duplicates_mode_frame); dupes_row.pack(fill=tk.X, pady=2)
        tk.Label(dupes_row, text="Folder:").pack(side=tk.LEFT); tk.Entry(dupes_row, textvariable=self.folder1_path).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(dupes_row, text="Browse...", command=self.select_folder1).pack(side=tk.LEFT)
        self.build_button_dupes1 = tk.Button(dupes_row, text="Build", command=lambda: self._build_metadata(1)); self.build_button_dupes1.pack(side=tk.LEFT, padx=(5,0))

        # ... (rest of UI is the same)
        options_frame = tk.LabelFrame(self.main_content_frame, text="Options", padx=10, pady=10); options_frame.pack(fill=tk.X, pady=10)
        match_frame = tk.LabelFrame(options_frame, text="Match/Find based on:", padx=5, pady=5); match_frame.pack(fill=tk.X)
        tk.Checkbutton(match_frame, text="Name", variable=self.compare_name).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(match_frame, text="Date", variable=self.compare_date).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(match_frame, text="Size", variable=self.compare_size).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(match_frame, text="Content (MD5 Hash)", variable=self.compare_content_md5).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(match_frame, text="Content (Histogram)", variable=self.compare_histogram).pack(side=tk.LEFT, padx=5)

        self.histogram_options_frame = tk.Frame(options_frame)

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

        sub_opts_frame = tk.Frame(options_frame); sub_opts_frame.pack(fill=tk.X, anchor=tk.W, pady=(5,0))
        self.include_subfolders_cb = tk.Checkbutton(sub_opts_frame, text="Include subfolders", variable=self.include_subfolders); self.include_subfolders_cb.pack(side=tk.LEFT)
        self.md5_warning_label = tk.Label(sub_opts_frame, text="Warning: Content comparison is slow.", fg="red")

        move_to_frame = tk.LabelFrame(options_frame, text="File Actions", padx=5, pady=5)
        move_to_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(move_to_frame, text="Move to Folder:").pack(side=tk.LEFT)
        tk.Entry(move_to_frame, textvariable=self.move_to_path).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(move_to_frame, text="Browse...", command=self.select_move_to_folder).pack(side=tk.LEFT)
        action_frame = tk.Frame(self.main_content_frame); action_frame.pack(fill=tk.X, pady=5)
        self.action_button = tk.Button(action_frame, text="Compare", command=self.run_action); self.action_button.pack()
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

        self._on_mode_change()
        self._toggle_histogram_options()
        self._update_histogram_threshold_ui()

    def _on_mode_change(self, *args):
        mode = self.app_mode.get()
        if mode == "compare":
            self.duplicates_mode_frame.pack_forget()
            self.compare_mode_frame.pack(fill=tk.X)
        else:
            self.compare_mode_frame.pack_forget()
            self.duplicates_mode_frame.pack(fill=tk.X)
        self.action_button.config(text="Compare")

    def _set_main_ui_state(self, state='normal'):
        def set_state_recursive(widget):
            if widget.winfo_class() == 'Menu': return
            try: widget.config(state=state)
            except tk.TclError: pass
            for child in widget.winfo_children(): set_state_recursive(child)
        set_state_recursive(self.main_content_frame)

    def _clear_all_settings(self):
        self.folder1_path.set(""); self.folder2_path.set(""); self.move_to_path.set(""); self.include_subfolders.set(False); self.compare_name.set(True)
        self.compare_date.set(False); self.compare_size.set(False); self.compare_content_md5.set(False)
        self.compare_histogram.set(False)
        self.histogram_method.set('Correlation')
        self.histogram_threshold.set('0.9')
        self.current_project_path = None; self.folder1_structure = None; self.folder2_structure = None
        self.root.title("Folder Comparison Tool")
        if hasattr(self, 'results_tree'):
            for i in self.results_tree.get_children(): self.results_tree.delete(i)

    def _new_project(self): self._clear_all_settings(); self._set_main_ui_state('normal'); self.root.title("New Project - Folder Comparison Tool")
    def select_folder1(self): path = filedialog.askdirectory(); self.folder1_path.set(path) if path else None
    def select_folder2(self): path = filedialog.askdirectory(); self.folder2_path.set(path) if path else None
    def select_move_to_folder(self): path = filedialog.askdirectory(); self.move_to_path.set(path) if path else None
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

    def _build_metadata(self, folder_num):
        build_buttons = [self.build_button_compare1, self.build_button_compare2, self.build_button_dupes1]

        try:
            # Disable buttons and show status
            for btn in build_buttons: btn.config(state='disabled')
            self.status_label.config(text=f"Building metadata for Folder {folder_num}...")
            self.root.update_idletasks()

            if not self._save_project():
                messagebox.showwarning("Save Cancelled", "Metadata build aborted because the project was not saved.")
                return
            path_var = self.folder1_path if folder_num == 1 else self.folder2_path
            path = path_var.get()
            if not path or not Path(path).is_dir():
                messagebox.showerror("Error", f"Please select a valid directory for Folder {folder_num}.")
                return

            structure = logic.build_folder_structure(path)
            if folder_num == 1: self.folder1_structure = structure
            else: self.folder2_structure = structure

            self.status_label.config(text=f"Metadata built for Folder {folder_num}. Saving project...")
            self.root.update_idletasks()
            self._save_project()
            messagebox.showinfo("Success", f"Metadata built and saved for Folder {folder_num}.")

        finally:
            # Re-enable buttons and clear status
            self.status_label.config(text="")
            for btn in build_buttons: btn.config(state='normal')

    def _gather_settings(self):
        settings = {
            "app_mode": self.app_mode.get(),
            "folder1_path": self.folder1_path.get(),
            "folder2_path": self.folder2_path.get(),
            "move_to_path": self.move_to_path.get(),
            "options": {
                "include_subfolders": self.include_subfolders.get(),
                "compare_name": self.compare_name.get(),
                "compare_date": self.compare_date.get(),
                "compare_size": self.compare_size.get(),
                "compare_content_md5": self.compare_content_md5.get(),
                "compare_histogram": self.compare_histogram.get(),
                "histogram_method": self.histogram_method.get(),
                "histogram_threshold": self.histogram_threshold.get()
            }
        }
        metadata = {}
        if self.folder1_structure:
            metadata["folder1"] = [node.to_dict() for node in self.folder1_structure]
        if self.folder2_structure:
            metadata["folder2"] = [node.to_dict() for node in self.folder2_structure]
        if metadata:
            settings["metadata"] = metadata
        return settings

    def _dict_to_structure(self, node_list):
        structure = []
        for node_dict in node_list:
            if node_dict['type'] == 'folder':
                node = FolderNode(Path(node_dict['fullpath']))
                node.content = self._dict_to_structure(node_dict.get('content', []))
                structure.append(node)
            elif node_dict['type'] == 'file':
                node = FileNode(Path(node_dict['fullpath']), node_dict.get('metadata'))
                structure.append(node)
        return structure

    def _save_project(self):
        if not self.current_project_path: return self._save_project_as()
        try:
            with open(self.current_project_path, 'w') as f: json.dump(self._gather_settings(), f, indent=4)
            return True
        except Exception as e: messagebox.showerror("Error", f"Could not save project file:\n{e}"); return False

    def _save_project_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".cfp", filetypes=[("Comparison Project Files", "*.cfp")])
        if not path: return False
        self.current_project_path = path; self.root.title(f"{Path(path).name} - Folder Comparison Tool")
        return self._save_project()

    def _load_project(self):
        path = filedialog.askopenfilename(filetypes=[("Comparison Project Files", "*.cfp")])
        if not path: return
        try:
            with open(path, 'r') as f: settings = json.load(f)
            self._clear_all_settings()
            self.app_mode.set(settings.get("app_mode", "compare"))
            self.folder1_path.set(settings.get("folder1_path", "")); self.folder2_path.set(settings.get("folder2_path", ""))
            self.move_to_path.set(settings.get("move_to_path", ""))
            opts = settings.get("options", {});
            for opt, val in opts.items():
                if hasattr(self, opt) and hasattr(getattr(self, opt), 'set'): getattr(self, opt).set(val)

            if "metadata" in settings:
                if "folder1" in settings["metadata"]: self.folder1_structure = self._dict_to_structure(settings["metadata"]["folder1"])
                if "folder2" in settings["metadata"]: self.folder2_structure = self._dict_to_structure(settings["metadata"]["folder2"])

            self.current_project_path = path; self.root.title(f"{Path(path).name} - Folder Comparison Tool")
            self._set_main_ui_state('normal')
        except Exception as e: messagebox.showerror("Error", f"Could not load project file:\n{e}")

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

    def _move_file(self, folder_num):
        iid, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return

        base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()
        dest_path_str = self.move_to_path.get()

        if not base_path_str or not dest_path_str:
            messagebox.showwarning("Warning", "Source or destination folder path is not set.")
            return

        try:
            source_path = Path(base_path_str) / relative_path_str
            dest_path = Path(dest_path_str) / source_path.name # move to folder, keep original name

            if not source_path.is_file():
                messagebox.showerror("Error", f"Source file does not exist:\n{source_path}")
                return

            if dest_path.exists():
                 if not messagebox.askyesno("Confirm Overwrite", f"Destination file already exists. Overwrite?\n\n{dest_path}"):
                     return

            confirm = messagebox.askyesno(
                "Confirm Move",
                f"Are you sure you want to move this file?\n\nFrom: {source_path}\nTo: {dest_path}"
            )
            if not confirm:
                return

            shutil.move(source_path, dest_path)
            self.results_tree.delete(iid)
            self.status_label.config(text=f"Moved: {source_path.name} to {dest_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not move file:\n{e}")

    def _delete_file(self, folder_num):
        iid, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return

        base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()
        if not base_path_str:
            messagebox.showwarning("Warning", f"Folder {folder_num} path is not set.")
            return

        try:
            full_path = Path(base_path_str) / relative_path_str
            if not full_path.is_file():
                messagebox.showerror("Error", f"File does not exist:\n{full_path}")
                return

            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to permanently delete this file?\n\n{full_path}"
            )
            if not confirm:
                return

            os.remove(full_path)
            self.results_tree.delete(iid)
            self.status_label.config(text=f"Deleted: {full_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not delete file:\n{e}")

    def _open_containing_folder(self, folder_num):
        _, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return

        base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()
        if not base_path_str:
            messagebox.showwarning("Warning", f"Folder {folder_num} path is not set.")
            return

        try:
            full_path = Path(base_path_str) / relative_path_str
            dir_path = full_path.parent

            if not dir_path.is_dir():
                messagebox.showerror("Error", f"Directory does not exist:\n{dir_path}")
                return

            if sys.platform == "win32":
                os.startfile(dir_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(dir_path)])
            else:
                subprocess.Popen(["xdg-open", str(dir_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")

    def _show_context_menu(self, event):
        iid = self.results_tree.identify_row(event.y)
        if not iid:
            return

        item = self.results_tree.item(iid)
        tags = item.get('tags', [])

        # Only show context menu for actual file rows
        if 'file_row' not in tags:
            return

        self.results_tree.selection_set(iid)
        context_menu = tk.Menu(self.root, tearoff=0)
        _, relative_path_str = self._get_relative_path_from_selection()

        # Determine preview state
        preview_state = tk.DISABLED
        if relative_path_str:
            file_ext = Path(relative_path_str).suffix.lower()
            is_image = file_ext in IMAGE_EXTENSIONS and PIL_AVAILABLE
            is_media = file_ext in VIDEO_EXTENSIONS or file_ext in AUDIO_EXTENSIONS
            if is_image or is_media:
                preview_state = tk.NORMAL

        # Determine move state
        move_state = tk.NORMAL if self.move_to_path.get() else tk.DISABLED

        # Build menu based on mode
        mode = self.app_mode.get()
        if mode == "compare":
            if preview_state == tk.NORMAL:
                context_menu.add_command(label="Preview from Folder 1", command=lambda: self._preview_file(1))
                context_menu.add_command(label="Preview from Folder 2", command=lambda: self._preview_file(2))
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
            if preview_state == tk.NORMAL:
                # In duplicates mode, there's only one folder, so we call with folder_num=1
                context_menu.add_command(label="Preview File", command=lambda: self._preview_file(1))
                context_menu.add_separator()
            context_menu.add_command(label="Open Containing Folder", command=lambda: self._open_containing_folder(1))
            context_menu.add_separator()
            context_menu.add_command(label="Move File...", command=lambda: self._move_file(1), state=move_state)
            context_menu.add_separator()
            context_menu.add_command(label="Delete File", command=lambda: self._delete_file(1))

        # Only post the menu if it has items in it
        if len(context_menu.children) > 0:
            context_menu.post(event.x_root, event.y_root)

    def _preview_file(self, folder_num):
        _, relative_path_str = self._get_relative_path_from_selection()
        if not relative_path_str:
            return

        base_path_str = self.folder1_path.get() if folder_num == 1 else self.folder2_path.get()
        if not base_path_str:
            messagebox.showwarning("Warning", f"Folder {folder_num} path is not set.")
            return

        full_path = Path(base_path_str) / relative_path_str
        if not full_path.is_file():
            messagebox.showerror("Error", f"File does not exist:\n{full_path}")
            return

        file_ext = full_path.suffix.lower()
        try:
            if file_ext in IMAGE_EXTENSIONS and PIL_AVAILABLE:
                # Display image in a new window
                win = tk.Toplevel(self.root)
                win.title(full_path.name)
                img = Image.open(full_path)
                img.thumbnail((800, 600)) # Resize for display
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(win, image=photo)
                label.image = photo # Keep a reference!
                label.pack()
            elif file_ext in VIDEO_EXTENSIONS or file_ext in AUDIO_EXTENSIONS:
                # Open with default system player
                if sys.platform == "win32":
                    os.startfile(full_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(full_path)])
                else:
                    subprocess.Popen(["xdg-open", str(full_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not preview file:\n{e}")


    def _update_filenode_metadata(self, structure, metadata_info, base_path):
        """Recursively update metadata of FileNodes in the structure."""
        base_path_obj = Path(base_path)
        for node in structure:
            if isinstance(node, FileNode):
                try:
                    relative_path = Path(node.fullpath).relative_to(base_path_obj)
                    if relative_path in metadata_info:
                        node.metadata.update(metadata_info[relative_path])
                except ValueError:
                    continue
            elif isinstance(node, FolderNode):
                self._update_filenode_metadata(node.content, metadata_info, base_path)

    def run_action(self):
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        opts = self._gather_settings()['options']
        mode = self.app_mode.get()

        try:
            # --- Metadata Generation and Persistence ---
            self.status_label.config(text="Calculating metadata...")
            self.root.update_idletasks()

            info1, info2 = None, None
            if self.folder1_structure:
                base_path1 = self.folder1_path.get()
                info1 = utils.flatten_structure(self.folder1_structure, base_path1, opts)
                self._update_filenode_metadata(self.folder1_structure, info1, base_path1)

            if self.folder2_structure:
                base_path2 = self.folder2_path.get()
                info2 = utils.flatten_structure(self.folder2_structure, base_path2, opts)
                self._update_filenode_metadata(self.folder2_structure, info2, base_path2)

            if self._save_project():
                self.status_label.config(text="Metadata calculated and project saved.")
            else:
                self.status_label.config(text="Metadata calculated, but project save failed.")
                messagebox.showwarning("Save Failed", "Could not save the project with new metadata.")

            # --- Strategy Execution ---
            if mode == "compare":
                if not info1 or not info2:
                    messagebox.showerror("Error", "Please build metadata for both folders before comparing.")
                    return

                results = find_common_strategy.run(info1, info2, opts)
                if not results:
                    self.results_tree.insert('', tk.END, values=("No matching files found.", "", ""), tags=('info_row',))
                else:
                    for file_info in results:
                        size = file_info.get('compare_size', 'N/A')
                        relative_path = file_info.get('relative_path', '')
                        file_name = Path(relative_path).name
                        self.results_tree.insert('', tk.END, values=(file_name, size, relative_path), tags=('file_row',))

            elif mode == "duplicates":
                if not info1:
                    messagebox.showerror("Error", "Please build metadata for the folder before finding duplicates.")
                    return

                results = find_duplicates_strategy.run(info1, opts)
                if not results:
                    self.results_tree.insert('', tk.END, values=("No duplicate files found.", "", ""), tags=('info_row',))
                else:
                    for i, group in enumerate(results, 1):
                        # Add a header row for the duplicate set
                        header_text = f"Duplicate Set {i} ({len(group)} files)"
                        parent = self.results_tree.insert('', tk.END, values=(header_text, "", ""), open=True, tags=('header_row',))
                        for file_info in group:
                            size = file_info.get('compare_size', 'N/A')
                            relative_path = file_info.get('relative_path', '')
                            file_name = Path(relative_path).name
                            self.results_tree.insert(parent, tk.END, values=(f"  {file_name}", size, relative_path), tags=('file_row',))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during comparison:\n{e}")
        finally:
            self.status_label.config(text="Ready.")
