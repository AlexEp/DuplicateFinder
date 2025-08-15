import tkinter as tk
from tkinter import filedialog

class FolderComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Comparison Tool")

        self.folder1_path = tk.StringVar()
        self.folder2_path = tk.StringVar()

        # Create and place widgets
        self.create_widgets()

    def create_widgets(self):
        # Frame for the application
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Folder 1 selection
        label1 = tk.Label(main_frame, text="Folder 1:")
        label1.grid(row=0, column=0, sticky=tk.W, pady=5)

        entry1 = tk.Entry(main_frame, textvariable=self.folder1_path, width=50)
        entry1.grid(row=0, column=1, padx=5)

        button1 = tk.Button(main_frame, text="Browse...", command=self.select_folder1)
        button1.grid(row=0, column=2)

        # Folder 2 selection
        label2 = tk.Label(main_frame, text="Folder 2:")
        label2.grid(row=1, column=0, sticky=tk.W, pady=5)

        entry2 = tk.Entry(main_frame, textvariable=self.folder2_path, width=50)
        entry2.grid(row=1, column=1, padx=5)

        button2 = tk.Button(main_frame, text="Browse...", command=self.select_folder2)
        button2.grid(row=1, column=2)

    def select_folder1(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder1_path.set(folder_selected)

    def select_folder2(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder2_path.set(folder_selected)

if __name__ == "__main__":
    root = tk.Tk()
    app = FolderComparisonApp(root)
    root.mainloop()
