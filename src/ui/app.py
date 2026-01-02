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
import database
from models import FileNode, FolderNode
from strategies import find_common_strategy, find_duplicates_strategy, utils
from config import config
from project_manager import ProjectManager
from interfaces.view_interface import IView
from .application_state import ApplicationState
from .components import StatusBar, SettingsPanel, FolderSelection, ResultsView

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
        x, y = 0, 0
        try:
            # This works for widgets with an insert cursor
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 20
        except (tk.TclError, TypeError):
            # This is a fallback for widgets like Listbox
            if event:
                x = event.x_root + 15
                y = event.y_root + 10
            else:
                # Last resort if event is not available
                x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
                y = self.widget.winfo_rooty() + self.widget.winfo_height()

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

class FolderComparisonApp(IView):
    def __init__(self, root):
        self._root = root
        self.root.title(config.get('ui.title', "Folder Comparison Tool"))
        
        # State
        self._state = ApplicationState()
        
        # Components (initialized in create_widgets)
        self._status_bar = None
        self._settings_panel = None
        self._folder_selection = None
        self._results_view = None
        
        self.controller = None # Will be set by the controller
        self.build_buttons = []
        
        # Keep references for controller's direct access (until controller is also refactored)
        self.folder_list_box = None
        self.results_tree = None
        self.progress_bar = None
        self.action_button = None

        # View variables (will be bound by controller)
        self.move_to_path = None
        self.file_type_filter = None
        self.include_subfolders = None
        self.compare_name = None
        self.compare_date = None
        self.compare_size = None
        self.compare_content_md5 = None
        self.compare_histogram = None
        self.histogram_method = None
        self.histogram_threshold = None
        self.compare_llm = None
        self.llm_similarity_threshold = None

    @property
    def root(self):
        return self._root

    def setup_ui(self):
        # --- Tracers ---
        # Note: Tracers for individual options are now handled inside SettingsPanel
        # for dynamic UI updates, or in AppController if needed for logic.
        from config import config

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

        file_type_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label=config.get('ui.labels.file_type', "File Type"), menu=file_type_menu)
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.all', "All"), variable=self.file_type_filter, value="all")
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.image', "Images"), variable=self.file_type_filter, value="image")
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.video', "Videos"), variable=self.file_type_filter, value="video")
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.audio', "Audio"), variable=self.file_type_filter, value="audio")
        file_type_menu.add_radiobutton(label=config.get('ui.file_types.document', "Documents"), variable=self.file_type_filter, value="document")

        # Main Layout: PanedWindow
        self._main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self._main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Panel (Folders and Options)
        left_panel = ttk.Frame(self._main_container)
        self._main_container.add(left_panel, weight=1)

        # Folder Selection Component
        self._folder_selection = FolderSelection(left_panel, self._on_folders_changed)
        self._folder_selection.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.folder_list_box = self._folder_selection._listbox # Backward compatibility

        # Settings Panel Component
        # We pass the existing tk.Variables from the view (which were bound by the controller)
        vars = {
            'file_type_filter': self.file_type_filter,
            'include_subfolders': self.include_subfolders,
            'compare_name': self.compare_name,
            'compare_size': self.compare_size,
            'compare_date': self.compare_date,
            'compare_content_md5': self.compare_content_md5,
            'compare_histogram': self.compare_histogram,
            'compare_llm': self.compare_llm,
        }
        self._settings_panel = SettingsPanel(left_panel, self._state.options, variables=vars)
        self._settings_panel.pack(fill=tk.X, pady=(0, 10))

        # Action Buttons
        action_frame = ttk.Frame(left_panel)
        action_frame.pack(fill=tk.X, pady=5)

        self.action_button = ttk.Button(action_frame, text="Compare", command=self.controller.run_action)
        self.action_button.pack(side=tk.TOP, fill=tk.X, pady=2)
        ToolTip(self.action_button, "Run the comparison or duplicate finding process.")

        # Right Panel (Results)
        right_panel = ttk.Frame(self._main_container)
        self._main_container.add(right_panel, weight=3)

        self._results_view = ResultsView(right_panel, 
                                        on_double_click=lambda iid: self._on_result_double_click(iid),
                                        on_right_click=self._show_context_menu)
        self._results_view.pack(fill=tk.BOTH, expand=True)
        self.results_tree = self._results_view.tree # Backward compatibility

        # Status Bar component
        self._status_bar = StatusBar(self.root)
        self._status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.progress_bar = self._status_bar._progress # Backward compatibility

        # Shortcuts
        self.root.bind('<Control-r>', lambda e: self.controller.run_action())

    def _on_folders_changed(self):
        """Handle folder list changes."""
        self.update_action_button_text()
        if self.controller:
            self.controller.on_folders_changed(self._folder_selection.get_paths()) if hasattr(self.controller, 'on_folders_changed') else None

    def update_action_button_text(self):
        """Update the text of the action button based on the number of folders."""
        if not self.action_button:
            return
        
        folder_paths = self._folder_selection.get_paths() if self._folder_selection else []
        if len(folder_paths) <= 1:
            self.action_button.config(text="Find Duplicates")
        else:
            self.action_button.config(text="Compare")

    def _on_result_double_click(self, iid):
        """Handle result activation."""
        if not iid:
            return

        item = self.results_tree.item(iid)
        # Try to get the relative path/filename from values
        text_to_copy = ""
        if item['values']:
            if len(item['values']) > 2 and item['values'][2]:
                text_to_copy = str(item['values'][2]).strip()
            else:
                text_to_copy = str(item['values'][0]).strip()

        if text_to_copy and "Duplicate Set" not in text_to_copy:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(text_to_copy)
                self.update_status(f"Copied to clipboard: {text_to_copy}")
            except tk.TclError:
                self.update_status("Error: Could not copy to clipboard.")

    def _on_file_type_change(self, *args):
        # Delegate to settings panel if it exists
        pass

    def set_ui_state(self, enabled: bool):
        """Enable/disable UI."""
        self._set_main_ui_state('normal' if enabled else 'disabled')

    def _set_main_ui_state(self, state='normal'):
        def set_state_recursive(widget):
            if widget.winfo_class() == 'Menu': return
            try: widget.config(state=state)
            except tk.TclError: pass
            for child in widget.winfo_children(): set_state_recursive(child)
        set_state_recursive(self._main_container)

    def remove_result_item(self, item_id: any):
        """Remove an item from the results tree."""
        if self.results_tree.exists(item_id):
            self.results_tree.delete(item_id)


    def update_status(self, message, progress_value=None):
        if self._status_bar:
            self._status_bar.set_message(message)
            if progress_value is not None:
                self._status_bar.set_progress(progress_value)
        else:
            # Fallback for during initialization or if not using component yet
            logger.debug(f"Status update (no status bar): {message}")

    def select_move_to_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.move_to_path.set(path)
            logger.info(f"Selected move-to folder: {path}")
    def _toggle_md5_warning(self, *args):
        # MD5 warning logic can be restored here if needed, 
        # but the label would need to be created first.
        pass

    def _toggle_histogram_options(self, *args):
        pass

    def _update_histogram_threshold_ui(self, *args):
        pass

    def _get_selected_file_info(self):
        """Gets the iid and full path for the selected file."""
        selection = self.results_tree.selection()
        if not selection:
            return None, None

        iid = selection[0]
        item = self.results_tree.item(iid)

        is_file_row = 'file_row' in item.get('tags', [])
        has_values = item.get('values')
        has_full_path = has_values and len(has_values) > 2 and has_values[2]

        if is_file_row and has_full_path:
            return iid, has_values[2].strip()

        return None, None

    def _move_file(self, iid=None, full_path_str=None, preview_window=None):
        if iid is None or full_path_str is None:
            iid, full_path_str = self._get_selected_file_info()
        if not iid: return

        dest_folder = self.move_to_path.get()
        if not dest_folder:
            messagebox.showwarning("Warning", "Move-to folder is not set.")
            return

        self.controller.move_file(iid, full_path_str, dest_folder)
        if preview_window: preview_window.destroy()

    def _delete_file(self, iid=None, full_path_str=None, preview_window=None):
        if iid is None or full_path_str is None:
            iid, full_path_str = self._get_selected_file_info()
        if not iid: return

        self.controller.delete_file(iid, full_path_str)
        if preview_window: preview_window.destroy()

    def _delete_file_from_preview(self, iid, full_path_str, preview_window):
        self._delete_file(iid, full_path_str, preview_window)

    def _move_file_from_preview(self, iid, full_path_str, preview_window):
        self._move_file(iid, full_path_str, preview_window)

    def _open_containing_folder(self):
        _, full_path_str = self._get_selected_file_info()
        if not full_path_str: return

        self.controller.open_folder(str(Path(full_path_str).parent))

    def _show_context_menu(self, event):
        iid = self.results_tree.identify_row(event.y)
        if not iid: return

        self.results_tree.selection_set(iid)
        item = self.results_tree.item(iid)
        if 'file_row' not in item.get('tags', []): return

        context_menu = tk.Menu(self.root, tearoff=0)
        _, full_path_str = self._get_selected_file_info()

        preview_state = tk.DISABLED
        if full_path_str:
            file_ext = Path(full_path_str).suffix.lower()
            is_image = file_ext in config.get("file_extensions.image", []) and PIL_AVAILABLE
            is_media = file_ext in config.get("file_extensions.video", []) or file_ext in config.get("file_extensions.audio", [])
            if is_image or is_media:
                preview_state = tk.NORMAL

        move_state = tk.NORMAL if self.move_to_path.get() else tk.DISABLED

        context_menu.add_command(label="Preview", command=self._preview_file, state=preview_state)
        context_menu.add_separator()
        context_menu.add_command(label="Open Containing Folder", command=self._open_containing_folder)
        context_menu.add_separator()
        context_menu.add_command(label="Move File", command=self._move_file, state=move_state)
        context_menu.add_separator()
        context_menu.add_command(label="Delete File", command=self._delete_file)

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
        has_path = has_values and len(has_values) > 3 and has_values[3]

        if is_file_row and has_path:
            return iid, has_values[3].strip()

        return None, None

    def _preview_file(self):
        iid, full_path_str = self._get_selected_file_info()
        if not iid: return

        full_path = Path(full_path_str)
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

                # Add buttons for delete and move
                button_frame = tk.Frame(win)
                button_frame.pack(pady=5)

                delete_btn = tk.Button(button_frame, text="Delete File", command=lambda: self._delete_file_from_preview(iid, full_path_str, win))
                delete_btn.pack(side=tk.LEFT, padx=5)

                move_btn = tk.Button(button_frame, text="Move File", command=lambda: self._move_file_from_preview(iid, full_path_str, win))
                move_btn.pack(side=tk.LEFT, padx=5)
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



    def show_new_project_dialog(self):
        self.controller.clear_all_settings()
        self.root.title("New Project - Folder Comparison Tool")

        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Project")
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.geometry("600x400")

        # Center the dialog
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_reqwidth()) / 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_reqheight()) / 2
        dialog.geometry(f"+{int(x)}+{int(y)}")

        dialog.protocol("WM_DELETE_WINDOW", lambda: self._cancel_new_project(dialog))

        self._set_main_ui_state('disabled')

        folder_selection = FolderSelection(dialog)
        folder_selection.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        def on_save():
            folders = folder_selection.get_paths()
            if not folders:
                messagebox.showwarning("No Folders", "Please add at least one folder.", parent=dialog)
                return

            path = filedialog.asksaveasfilename(
                parent=dialog,
                defaultextension=".cfp-db",
                filetypes=[("Comparison Project DB", "*.cfp-db")]
            )
            if not path:
                return

            self.controller.project_manager.create_new_project_file(path, folders)
            self._folder_selection.set_paths(folders)

            self.update_action_button_text()
            self._set_main_ui_state('normal')
            dialog.destroy()

        save_button = tk.Button(button_frame, text="Save Project and Continue", command=on_save)
        save_button.pack()

        self.root.wait_window(dialog)

    def _cancel_new_project(self, dialog):
        dialog.destroy()
        self._set_main_ui_state('normal')

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

class ToolTip:
    """A simple tooltip class."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()
