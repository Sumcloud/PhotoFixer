import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
import shutil

# Global variables
csv_filepath = ""
article_folder_path = ""
product_group_path = ""
delimiter = ";"
allowed_images = []

act_pg_art = []

def select_folder(entry_var):
    folder_path = filedialog.askdirectory()
    entry_var.set(folder_path)

def select_csv_file(entry_var):
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    global csv_filepath
    csv_filepath = file_path
    entry_var.set(file_path)

def set_pg_folder(entry_var):
    select_folder(entry_var)
    global product_group_path
    product_group_path = entry_var.get()

def set_art_folder(entry_var):
    select_folder(entry_var)
    global article_folder_path
    article_folder_path = entry_var.get()

def sort_treeview(tree, col, reverse=False):
    """Sort treeview by given column."""
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    
    # Sort boolean values correctly
    if col == "FileFound":
        data.sort(reverse=reverse, key=lambda x: (x[0].lower(), x[0]))
    else:
        data.sort(reverse=reverse)

    for index, (val, child) in enumerate(data):
        tree.move(child, '', index)

    tree.heading(col, command=lambda: sort_treeview(tree, col, not reverse))


def read_csv(filepath_csv: str, delimiter: str) -> dict:
    """Reads the CSV and creates a dictionary entry for each product group where the value is the corresponding article numbers."""
    pg_art = {}
    with open(filepath_csv, mode='r', newline='') as file:
        csv_reader = csv.reader(file, delimiter=delimiter)
        next(csv_reader)  # Skip header
        for line in csv_reader:
            pg_art.setdefault(line[0], []).append(line[1])
    return pg_art

def generate_article_filenames(pg_art: dict, article_folder_path: str) -> list:
    """Reads a dictionary and sends back a list of confirmed existing filenames in the form of a tuple."""
    def generate_filename(article_number: str, picture_size: str) -> str:
        return f"{article_folder_path}/A{article_number}_H_{picture_size}.jpg"

    results = []
    global allowed_images
    for product_group, articles in pg_art.items():
        found_file = None
        for size in allowed_images:
            for article in articles:
                filename = generate_filename(article, str(size))
                if os.path.exists(filename):
                    found_file = (product_group, article, filename, True)
                    break
            if found_file:
                break
        if not found_file:
            found_file = (product_group, "", "", False)
        results.append(found_file)
    return results

def export_to_csv(act_pg_art, delimiter):
    export_filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if export_filepath:
        with open(export_filepath, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=delimiter)
            writer.writerow(["ProductGroup", "ArticleNumber", "Filename", "FileFound"])
            writer.writerows(act_pg_art)

def move_files(act_pg_art, article_folder_path, product_group_path):
    for entry in act_pg_art:
        if entry[3]:
            shutil.copy(entry[2], product_group_path)
            os.rename(f"{product_group_path}/{os.path.basename(entry[2])}", f"{product_group_path}/{entry[0]}.jpg")
    messagebox.showinfo("Files Copied!", "Files have been successfully copied.")

def main():
    window = tk.Tk()
    window.title("Productgroup photos")
    window.resizable(False, False)
    window.geometry("650x350")

    frame = tk.Frame(window)
    frame.pack()

    def validate_allowed_image_input():
        try:
            allowed_images_str = allowed_image_formats.get().strip()
            if not allowed_images_str:
                messagebox.showerror("Error", "No input provided.")
                return False
            allowed_images_list = list(map(int, allowed_images_str.split(',')))
            if all(isinstance(x, int) for x in allowed_images_list):
                messagebox.showinfo("Succes", "Input is valid")
                global allowed_images
                allowed_images = allowed_images_list
                return True
            else:
                messagebox.showerror("Error", "Invalid input. Please enter comma-separated integers.")
                return False
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please enter comma-separated integers.")
            return False

    def set_delimiter(value):
        global delimiter
        delimiter = value

    def result_table_popup():
        global csv_filepath, act_pg_art, allowed_images
        allowed_images_str = allowed_image_formats.get().strip()
        if not allowed_images_str:
            messagebox.showerror("Error", "No input provided.")
            return

        try:
            allowed_images_list = list(map(int, allowed_images_str.split(',')))
            if all(isinstance(x, int) for x in allowed_images_list):
                allowed_images = allowed_images_list
            else:
                messagebox.showerror("Error", "Invalid input. Please enter comma-separated integers.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please enter comma-separated integers.")
            return

        if not act_pg_art:
            csv_content = read_csv(csv_filepath, delimiter)
            act_pg_art = generate_article_filenames(csv_content, article_folder_path)

        top = tk.Toplevel(window)
        top.geometry("800x1000")

        tree = ttk.Treeview(top, columns=("ProductGroup", "ArticleNumber", "Filename", "FileFound"), show="headings")
        tree.pack(fill="both", expand=True)

        for col in ("ProductGroup", "ArticleNumber", "Filename", "FileFound"):
            tree.heading(col, text=col, command=lambda c=col: sort_treeview(tree, c))

        for item in act_pg_art:
            item = list(item)
            item[3] = "Yes" if item[3] else "No"
            tree.insert("", "end", values=item)

        scrollbar = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y", expand=False)
        tree.configure(yscrollcommand=scrollbar.set)

        tk.Button(top, text="Export", command=lambda: export_to_csv(act_pg_art, delimiter)).pack(pady=10)


    tk.Label(frame, text="Delimiter:").grid(row=0, column=0, sticky="w")
    delimiter_var = tk.StringVar()
    delimiter_options = [';', ',', ':', '/', '|']
    tk.OptionMenu(frame, delimiter_var, *delimiter_options, command=set_delimiter).grid(row=0, column=1, sticky="w", padx=5)
    delimiter_var.set(delimiter_options[0])

    tk.Label(frame, text="Image formats:").grid(row=1, column=0, sticky='w')
    allowed_image_formats = tk.StringVar()
    tk.Entry(frame, textvariable=allowed_image_formats, state='normal', width=40).grid(row=1, column=1, sticky='w', padx=5)
    tk.Button(frame, text='Validate', command=validate_allowed_image_input).grid(row=1, column=2, sticky='w')
    tk.Label(frame, text='In order, comma-separated').grid(row=1, column=3, sticky='w', padx=5)

    tk.Label(frame, text="CSV File:").grid(row=2, column=0, sticky="w")
    csv_file_entry_var = tk.StringVar()
    tk.Entry(frame, textvariable=csv_file_entry_var, state="readonly", width=40).grid(row=2, column=1, sticky="w", padx=5)
    tk.Button(frame, text="Browse", command=lambda: select_csv_file(csv_file_entry_var)).grid(row=2, column=2, sticky="w")

    tk.Label(frame, text="Article folder path:").grid(row=3, column=0, sticky="w")
    article_folder_entry_var = tk.StringVar()
    tk.Entry(frame, textvariable=article_folder_entry_var, state="readonly", width=40).grid(row=3, column=1, sticky="w", padx=5)
    tk.Button(frame, text="Browse", command=lambda: set_art_folder(article_folder_entry_var)).grid(row=3, column=2, sticky="w")

    tk.Label(frame, text="Product group folder path:").grid(row=4, column=0, sticky="w")
    product_group_entry_var = tk.StringVar()
    tk.Entry(frame, textvariable=product_group_entry_var, state="readonly", width=40).grid(row=4, column=1, sticky="w", padx=5)
    tk.Button(frame, text="Browse", command=lambda: set_pg_folder(product_group_entry_var)).grid(row=4, column=2, sticky="w")

    tk.Button(frame, text="Results", command=result_table_popup, padx=40, pady=20).grid(row=5, columnspan=3, pady=15)

    tk.Button(frame, text="Move files!", command=lambda: move_files(act_pg_art, article_folder_path, product_group_path), pady=20, padx=40).grid(row=6, columnspan=3, pady=15)

    window.mainloop()

if __name__ == '__main__':
    main()
