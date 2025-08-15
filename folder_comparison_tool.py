import tkinter as tk
from tkinter import filedialog, ttk

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
        results_frame = tk.LabelFrame(main_frame, text="Results", padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.results_text = tk.Text(results_frame, height=10, width=50)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(results_frame, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)


    def select_folder1(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder1_path.set(folder_selected)

    def select_folder2(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder2_path.set(folder_selected)

    def compare_folders(self):
        # Placeholder for comparison logic
        self.results_text.delete('1.0', tk.END)  # Clear previous results
        self.results_text.insert(tk.END, "Comparison started...\n")
        self.results_text.insert(tk.END, f"Folder 1: {self.folder1_path.get()}\n")
        self.results_text.insert(tk.END, f"Folder 2: {self.folder2_path.get()}\n")
        self.results_text.insert(tk.END, f"Include subfolders: {self.include_subfolders.get()}\n")
        self.results_text.insert(tk.END, f"Match by Name: {self.compare_name.get()}\n")
        self.results_text.insert(tk.END, f"Match by Date: {self.compare_date.get()}\n")
        self.results_text.insert(tk.END, f"Match by Size: {self.compare_size.get()}\n")
        self.results_text.insert(tk.END, f"File type: {self.file_type.get()}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = FolderComparisonApp(root)
    root.mainloop()
