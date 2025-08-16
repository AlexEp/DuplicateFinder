import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
from pathlib import Path
import json
import logic

class FolderComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Comparison Tool")
        self.current_project_path = None
        self.folder1_structure = None
        self.folder2_structure = None

        self.folder1_path = tk.StringVar()
        self.folder2_path = tk.StringVar()

        # Comparison options
        self.include_subfolders = tk.BooleanVar()
        self.compare_name = tk.BooleanVar(value=True)
        self.compare_date = tk.BooleanVar()
        self.compare_size = tk.BooleanVar()
        self.compare_content = tk.BooleanVar()
        self.file_type = tk.StringVar(value='All')

        self.compare_content.trace_add('write', self._toggle_md5_warning)

        # Create and place widgets
        self.create_widgets()
        # Start with the main UI disabled
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

        # --- Main Content Frame ---
        # This frame will hold all widgets that should be enabled/disabled
        self.main_content_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Folder Selection ---
        folder_frame = tk.LabelFrame(self.main_content_frame, text="Select Folders", padx=10, pady=10)
        folder_frame.pack(fill=tk.X, expand=True)
        # ... (rest of the widgets go inside self.main_content_frame)

        label1 = tk.Label(folder_frame, text="Folder 1:")
        label1.grid(row=0, column=0, sticky=tk.W, pady=5)
        # ... (and so on for all other widgets)
        entry1 = tk.Entry(folder_frame, textvariable=self.folder1_path, width=50)
        entry1.grid(row=0, column=1, padx=5)
        button1 = tk.Button(folder_frame, text="Browse...", command=self.select_folder1)
        button1.grid(row=0, column=2)
        label2 = tk.Label(folder_frame, text="Folder 2:")
        label2.grid(row=1, column=0, sticky=tk.W, pady=5)
        entry2 = tk.Entry(folder_frame, textvariable=self.folder2_path, width=50)
        entry2.grid(row=1, column=1, padx=5)
        button2 = tk.Button(folder_frame, text="Browse...", command=self.select_folder2)
        button2.grid(row=1, column=2)

        # --- Comparison Options ---
        options_frame = tk.LabelFrame(self.main_content_frame, text="Options", padx=10, pady=10)
        options_frame.pack(fill=tk.X, expand=True, pady=10)
        match_frame = tk.LabelFrame(options_frame, text="Match files based on:", padx=5, pady=5)
        match_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        cb_name = tk.Checkbutton(match_frame, text="Name", variable=self.compare_name)
        cb_name.pack(side=tk.LEFT, padx=5)
        cb_date = tk.Checkbutton(match_frame, text="Date", variable=self.compare_date)
        cb_date.pack(side=tk.LEFT, padx=5)
        cb_size = tk.Checkbutton(match_frame, text="Size", variable=self.compare_size)
        cb_size.pack(side=tk.LEFT, padx=5)
        cb_content = tk.Checkbutton(match_frame, text="Content (MD5)", variable=self.compare_content)
        cb_content.pack(side=tk.LEFT, padx=5)
        cb_subfolders = tk.Checkbutton(options_frame, text="Include subfolders", variable=self.include_subfolders)
        cb_subfolders.grid(row=1, column=0, sticky=tk.W, pady=5)
        file_type_label = tk.Label(options_frame, text="File types:")
        file_type_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        file_type_combo = ttk.Combobox(options_frame, textvariable=self.file_type, values=['All', 'Images'], state='readonly')
        file_type_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.md5_warning_label = tk.Label(options_frame, text="Warning: Content comparison can be slow.", fg="red")

        # --- Action Buttons ---
        action_frame = tk.Frame(self.main_content_frame, pady=10)
        action_frame.pack(fill=tk.X, expand=True)
        self.compare_button = tk.Button(action_frame, text="Compare", command=self.compare_folders)
        self.compare_button.pack()

        # --- Results Display ---
        results_frame = tk.LabelFrame(self.main_content_frame, text="Results (double-click to open folder)", padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.results_tree = ttk.Treeview(results_frame, columns=('File',), show='headings')
        self.results_tree.heading('File', text='File')
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(results_frame, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.config(yscrollcommand=scrollbar.set)
        self.results_tree.bind('<Double-1>', self._on_double_click)

    def _set_main_ui_state(self, state='normal'):
        """Recursively sets the state of all widgets in the main content frame."""
        for widget in self.main_content_frame.winfo_children():
            # Check if the widget is a container like a Frame or LabelFrame
            if isinstance(widget, (tk.Frame, tk.LabelFrame)):
                for child in widget.winfo_children():
                    try:
                        child.config(state=state)
                    except tk.TclError:
                        # Some widgets like Labels might not have a 'state' option
                        pass
            else:
                 try:
                    widget.config(state=state)
                 except tk.TclError:
                    pass

    def _clear_all_settings(self):
        """Resets all variables to their default state."""
        self.folder1_path.set("")
        self.folder2_path.set("")
        self.include_subfolders.set(False)
        self.compare_name.set(True)
        self.compare_date.set(False)
        self.compare_size.set(False)
        self.compare_content.set(False)
        self.file_type.set("All")
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)
        self.current_project_path = None
        self.folder1_structure = None
        self.folder2_structure = None
        self.root.title("Folder Comparison Tool")

    def _new_project(self):
        self._clear_all_settings()
        self._set_main_ui_state('normal')
        self.root.title("New Project - Folder Comparison Tool")

    def select_folder1(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder1_path.set(folder_selected)

    def select_folder2(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder2_path.set(folder_selected)

    def _on_double_click(self, event):
        item_id = self.results_tree.focus()
        if not item_id: return
        item = self.results_tree.item(item_id)
        relative_path = item['values'][0]
        folder1 = self.folder1_path.get()
        if not folder1: return
        full_path = Path(folder1) / relative_path
        containing_folder = full_path.parent
        try:
            os.startfile(containing_folder)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")

    def _toggle_md5_warning(self, *args):
        if self.compare_content.get():
            self.md5_warning_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=5)
        else:
            self.md5_warning_label.grid_forget()

    def _gather_settings(self):
        return {
            "folder1_path": self.folder1_path.get(),
            "folder2_path": self.folder2_path.get(),
            "options": {
                "include_subfolders": self.include_subfolders.get(),
                "compare_name": self.compare_name.get(),
                "compare_date": self.compare_date.get(),
                "compare_size": self.compare_size.get(),
                "compare_content": self.compare_content.get(),
                "file_type": self.file_type.get()
            }
        }

    def _save_project(self):
        if not self.current_project_path:
            return self._save_project_as()

        settings = self._gather_settings()
        try:
            with open(self.current_project_path, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save project file:\n{e}")
            return False

    def _save_project_as(self):
        project_path = filedialog.asksaveasfilename(
            defaultextension=".cfp",
            filetypes=[("Comparison Project Files", "*.cfp"), ("All Files", "*.*")]
        )
        if not project_path:
            return False

        self.current_project_path = project_path
        self.root.title(f"{Path(project_path).name} - Folder Comparison Tool")
        return self._save_project()

    def _load_project(self):
        project_path = filedialog.askopenfilename(
            filetypes=[("Comparison Project Files", "*.cfp"), ("All Files", "*.*")]
        )
        if not project_path:
            return

        try:
            with open(project_path, 'r') as f:
                settings = json.load(f)

            self._clear_all_settings()
            self.folder1_path.set(settings.get("folder1_path", ""))
            self.folder2_path.set(settings.get("folder2_path", ""))

            opts = settings.get("options", {})
            self.include_subfolders.set(opts.get("include_subfolders", False))
            self.compare_name.set(opts.get("compare_name", True))
            self.compare_date.set(opts.get("compare_date", False))
            self.compare_size.set(opts.get("compare_size", False))
            self.compare_content.set(opts.get("compare_content", False))
            self.file_type.set(opts.get("file_type", "All"))

            self.current_project_path = project_path
            self.root.title(f"{Path(project_path).name} - Folder Comparison Tool")
            self._set_main_ui_state('normal')
            messagebox.showinfo("Success", f"Project loaded from {project_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not load project file:\n{e}")

    def compare_folders(self):
        if not self._save_project():
             messagebox.showwarning("Save Cancelled", "Comparison aborted because the project was not saved.")
             return

        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        folder1 = self.folder1_path.get()
        folder2 = self.folder2_path.get()

        opts = self._gather_settings()['options']

        if not folder1 or not folder2:
            messagebox.showerror("Error", "Please select both folders.")
            return

        if not any([opts['by_name'], opts['by_date'], opts['by_size'], opts['by_content']]):
             messagebox.showerror("Error", "Please select at least one matching criterion.")
             return

        # Build the in-memory file system structure
        self.folder1_structure = logic.build_folder_structure(folder1)
        self.folder2_structure = logic.build_folder_structure(folder2)
        messagebox.showinfo("In-Memory Scan", "Folder structures have been scanned into memory.")

        common_files = logic.find_common_files(folder1, folder2, opts)

        if not common_files:
            self.results_tree.insert('', tk.END, values=("No common files found.",))
        else:
            for file_path in common_files:
                self.results_tree.insert('', tk.END, values=(file_path,))
