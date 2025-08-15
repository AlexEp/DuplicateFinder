import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
from pathlib import Path
import logic

class FolderComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Comparison Tool")

        self.folder1_path = tk.StringVar()
        self.folder2_path = tk.StringVar()

        # Comparison options
        self.include_subfolders = tk.BooleanVar()
        self.compare_name = tk.BooleanVar(value=True)
        self.compare_date = tk.BooleanVar()
        self.compare_size = tk.BooleanVar()
        self.file_type = tk.StringVar(value='All')


        # Create and place widgets
        self.create_widgets()

    def create_widgets(self):
        # Frame for the application
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Folder Selection ---
        folder_frame = tk.LabelFrame(main_frame, text="Select Folders", padx=10, pady=10)
        folder_frame.pack(fill=tk.X, expand=True)

        label1 = tk.Label(folder_frame, text="Folder 1:")
        label1.grid(row=0, column=0, sticky=tk.W, pady=5)

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
        options_frame = tk.LabelFrame(main_frame, text="Options", padx=10, pady=10)
        options_frame.pack(fill=tk.X, expand=True, pady=10)

        # Match criteria
        match_frame = tk.LabelFrame(options_frame, text="Match files based on:", padx=5, pady=5)
        match_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)

        cb_name = tk.Checkbutton(match_frame, text="Name", variable=self.compare_name)
        cb_name.pack(side=tk.LEFT, padx=5)

        cb_date = tk.Checkbutton(match_frame, text="Date", variable=self.compare_date)
        cb_date.pack(side=tk.LEFT, padx=5)

        cb_size = tk.Checkbutton(match_frame, text="Size", variable=self.compare_size)
        cb_size.pack(side=tk.LEFT, padx=5)

        # Other options
        cb_subfolders = tk.Checkbutton(options_frame, text="Include subfolders", variable=self.include_subfolders)
        cb_subfolders.grid(row=1, column=0, sticky=tk.W, pady=5)

        file_type_label = tk.Label(options_frame, text="File types:")
        file_type_label.grid(row=2, column=0, sticky=tk.W, pady=5)

        file_type_combo = ttk.Combobox(options_frame, textvariable=self.file_type, values=['All', 'Images'], state='readonly')
        file_type_combo.grid(row=2, column=1, sticky=tk.W, pady=5)


        # --- Action Buttons ---
        action_frame = tk.Frame(main_frame, pady=10)
        action_frame.pack(fill=tk.X, expand=True)

        compare_button = tk.Button(action_frame, text="Compare", command=self.compare_folders)
        compare_button.pack()

        # --- Results Display ---
        results_frame = tk.LabelFrame(main_frame, text="Results (double-click to open folder)", padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.results_tree = ttk.Treeview(results_frame, columns=('File',), show='headings')
        self.results_tree.heading('File', text='File')
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(results_frame, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.config(yscrollcommand=scrollbar.set)

        self.results_tree.bind('<Double-1>', self._on_double_click)


    def select_folder1(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder1_path.set(folder_selected)

    def select_folder2(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder2_path.set(folder_selected)

    def _on_double_click(self, event):
        """Event handler for double-clicking a result."""
        item_id = self.results_tree.focus()
        if not item_id:
            return

        item = self.results_tree.item(item_id)
        relative_path = item['values'][0]

        folder1 = self.folder1_path.get()
        if not folder1:
            return

        # Use Path for robust path manipulation
        full_path = Path(folder1) / relative_path
        containing_folder = full_path.parent

        try:
            os.startfile(containing_folder)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")

    def compare_folders(self):
        # Clear previous results
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

        # Get paths and options
        folder1 = self.folder1_path.get()
        folder2 = self.folder2_path.get()
        recursive = self.include_subfolders.get()

        # Validate paths
        if not folder1 or not folder2:
            messagebox.showerror("Error", "Please select both folders.")
            return

        # For now, only implement "compare by name" as requested
        if not self.compare_name.get():
            messagebox.showinfo("Info", "Comparison is currently only implemented for matching by name.")
            return

        common_files = logic.find_common_files(folder1, folder2, recursive)

        # Populate results
        if not common_files:
            self.results_tree.insert('', tk.END, values=("No common files found.",))
        else:
            for file_path in common_files:
                self.results_tree.insert('', tk.END, values=(file_path,))
