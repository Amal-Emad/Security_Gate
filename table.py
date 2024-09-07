import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import csv
from datetime import datetime

base_csv_dir = "csv_files"
saved_plate_dir = 'D:\\oman_car_plates\\saved_plates'

if not os.path.exists(base_csv_dir):
    os.makedirs(base_csv_dir)

# Function to get today's directory and CSV file
def get_today_csv_path():
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_dir = os.path.join(base_csv_dir, today_str)
    if not os.path.exists(today_dir):
        os.makedirs(today_dir)
    csv_path = os.path.join(today_dir, 'plates_data.csv')
    return csv_path

# Function to load data from today's CSV
def load_data_from_csv():
    data = []
    csv_path = get_today_csv_path()
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)
    return data

# Function to write data to today's CSV
def write_data_to_csv(data):
    csv_path = get_today_csv_path()
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys() if data else ['name', 'timestamp', 'plate_file'])
        writer.writeheader()
        writer.writerows(data)

# Function to add a name to the selected plate
def add_name(plate_file, table, item):
    name = simpledialog.askstring("Input", "Enter the person's name:")
    if name:
        data_list = load_data_from_csv()

        # Check if the name already exists
        for record in data_list:
            if record['name'] == name:
                messagebox.showerror("Error", f"The name '{name}' already exists.")
                return

        # Check if the plate file already exists
        for record in data_list:
            if record['plate_file'] == plate_file:
                messagebox.showerror("Error", "This plate image already exists.")
                return

        # If not, add the name to the CSV
        timestamp = plate_file.split('_')[1].replace(".png", "")
        data = {'name': name, 'timestamp': timestamp, 'plate_file': plate_file}
        data_list.append(data)

        write_data_to_csv(data_list)
        
        # Update Treeview directly
        table.item(item, values=(plate_file, timestamp, name))
        messagebox.showinfo("Info", "Name added successfully.")


# Function to save the selected plate image
def save_plate(plate_file):
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")], initialfile=os.path.basename(plate_file))
    if save_path:
        os.rename(plate_file, save_path)
        messagebox.showinfo("Info", "Plate image saved.")

# Function to delete the selected plate image
def delete_plate(plate_file, table, item):
    os.remove(plate_file)
    table.delete(item)
    
    # Remove from CSV file
    data_list = load_data_from_csv()
    data_list = [record for record in data_list if record['plate_file'] != plate_file]
    
    write_data_to_csv(data_list)

    messagebox.showinfo("Info", "Plate image deleted.")

# Function to save all plate data as a CSV file
def save_as_csv(data):
    save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="plates_data.csv")
    if save_path:
        write_data_to_csv(data)
        messagebox.showinfo("Info", "CSV file saved.")

# Function to delete all plates from the table
def delete_all_plates(table):
    for item in table.get_children():
        plate_file = table.item(item, "values")[0]
        os.remove(os.path.join(saved_plate_dir, plate_file))
    table.delete(*table.get_children())
    
    # Clear CSV file
    csv_path = get_today_csv_path()
    open(csv_path, 'w').close()
    
    messagebox.showinfo("Info", "All plates deleted.")

# Function to display the table of saved plates
def show_saved_plates(root):
    plate_files = [f for f in os.listdir(saved_plate_dir) if os.path.isfile(os.path.join(saved_plate_dir, f))]

    top = tk.Toplevel(root)
    top.title("Saved Plates")
    top.geometry("1000x600")

    table_frame = tk.Frame(top)
    table_frame.pack(fill=tk.BOTH, expand=True)

    # Create a style for the Treeview
    style = ttk.Style()

    # Configure the Treeview background and foreground
    style.configure("Treeview",
                    background="beige",
                    foreground="darkgreen",
                    fieldbackground="beige")

    # Configure the Treeview heading
    style.configure("Treeview.Heading",
                    background="darkgreen",
                    foreground="beige")

    # Configure the Treeview selection colors
    style.map("Treeview",
            background=[('selected', 'darkolivegreen')],
            foreground=[('selected', 'beige')])

    table = ttk.Treeview(table_frame, columns=("Image", "Timestamp", "Name"), show="headings", style="Treeview")
    table.heading("Image", text="Plate Image")
    table.heading("Timestamp", text="Timestamp")
    table.heading("Name", text="Name")

    table.column("Image", anchor=tk.CENTER, width=300)
    table.column("Timestamp", anchor=tk.CENTER, width=200)
    table.column("Name", anchor=tk.CENTER, width=200)

    scroll_y = tk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    table.configure(yscroll=scroll_y.set)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    table.pack(fill=tk.BOTH, expand=True)

    # Refresh the data and update the table
    data = load_data_from_csv()
    table.delete(*table.get_children())  # Clear existing data

    for plate_file in plate_files:
        plate_path = os.path.join(saved_plate_dir, plate_file)
        timestamp = plate_file.split('_')[1].replace(".png", "")
        img = Image.open(plate_path)
        img.thumbnail((200, 200))
        img_tk = ImageTk.PhotoImage(img)

        # Find existing data for the plate_file
        name = ""
        for record in data:
            if record['plate_file'] == plate_file:
                name = record['name']
                break
        
        table.insert('', tk.END, iid=plate_file, values=(plate_file, timestamp, name), image=img_tk)
    
    # Function to handle row selection
    def on_select(event):
        item = table.selection()[0]
        plate_file = table.item(item, "values")[0]

        # Clear previous widgets
        for widget in top.winfo_children():
            if isinstance(widget, tk.Frame) and widget != table_frame:
                widget.destroy()

        # Display the selected plate image and controls
        img_frame = tk.Frame(top)
        img_frame.pack(pady=5)

        img = Image.open(os.path.join(saved_plate_dir, plate_file))
        img.thumbnail((300, 300))
        img_tk = ImageTk.PhotoImage(img)

        img_label = tk.Label(img_frame, image=img_tk)
        img_label.image = img_tk  # Keep reference to prevent garbage collection
        img_label.pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=5)

        save_btn = tk.Button(btn_frame, text="Save As PNG", command=lambda: save_plate(os.path.join(saved_plate_dir, plate_file)))
        save_btn.pack(side=tk.LEFT, padx=5)

        add_name_btn = tk.Button(btn_frame, text="Add Name", command=lambda: add_name(os.path.join(saved_plate_dir, plate_file), table, item))
        add_name_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(btn_frame, text="Delete", command=lambda: delete_plate(os.path.join(saved_plate_dir, plate_file), table, item))
        delete_btn.pack(side=tk.LEFT, padx=5)

        save_csv_btn = tk.Button(btn_frame, text="Save As CSV", command=lambda: save_as_csv(load_data_from_csv()))
        save_csv_btn.pack(side=tk.LEFT, padx=5)

        delete_all_btn = tk.Button(btn_frame, text="Delete All", command=lambda: delete_all_plates(table))
        delete_all_btn.pack(side=tk.LEFT, padx=5)

    table.bind('<<TreeviewSelect>>', on_select)

# Integrating with the main Tkinter application
def main():
    root = tk.Tk()
    root.title("Plate Detection Application")

    # Set up main window and controls here
    show_saved_plates_btn = tk.Button(root, text="Show Saved Plates", command=lambda: show_saved_plates(root))
    show_saved_plates_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
