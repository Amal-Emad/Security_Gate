import tkinter as tk
from tkinter import filedialog, Toplevel, messagebox
from PIL import Image, ImageTk
import cv2
import os
from datetime import datetime
from model import PipelineModel
import threading

pipeline = PipelineModel(
    car_model_path=r'D:\oman_car_plates\MODELS\vehicle_detection.pt',
    plate_model_path=r'D:\oman_car_plates\MODELS\licensePlate.pt',
    char_model_path=r'D:\oman_car_plates\MODELS\best(2).pt'
)

cap = None
file_path = None
is_video = False
show_plate = True
frame_skip = 2  # Process every 2nd frame
frame_count = 0
saved_plate_dir = "saved_plates"
os.makedirs(saved_plate_dir, exist_ok=True)

def process_frame(frame):
    car_boxes, plates, characters = pipeline.detect(frame)
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    for box in car_boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(img_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)

    plate_img = None
    if plates:
        px1, py1, px2, py2, plate_crop = plates[0]
        cv2.rectangle(img_rgb, (px1, py1), (px2, py2), (255, 0, 0), 2)
        plate_img = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2RGB)
        # Save the plate image with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plate_filename = os.path.join(saved_plate_dir, f"plate_{timestamp}.png")
        cv2.imwrite(plate_filename, cv2.cvtColor(plate_crop, cv2.COLOR_RGB2BGR))
    
    return img_rgb, plate_img, characters

def update_results(characters):
    result_text = "Detection Results:\n"
    filtered_labels = []
    
    valid_labels = set(map(str, range(10)))  # Numbers 0-9
    valid_labels.update(chr(c) for c in range(65, 91))  # Letters A-Z

    if characters:
        for _, _, _, _, label in characters:
            if label in valid_labels:
                filtered_labels.append(label)
    
    if filtered_labels:
        result_text += " ".join(filtered_labels)
    else:
        result_text += "No valid characters detected."
    
    result_label.config(text=result_text)

def frame_processing_thread():
    global cap, file_path, is_video, show_plate, frame_count

    while True:
        if is_video:
            ret, frame = cap.read()
            if not ret:
                cap.release()
                is_video = False
                result_label.config(text="Video ended or failed to capture frame")
                break

            if frame_count % frame_skip == 0:
                img_rgb, plate_img, characters = process_frame(frame)
                
                img_tk = ImageTk.PhotoImage(Image.fromarray(img_rgb))
                video_frame_left.config(image=img_tk)
                video_frame_left.image = img_tk

                if show_plate and plate_img is not None:
                    plate_img_tk = ImageTk.PhotoImage(Image.fromarray(plate_img))
                    video_frame_right.config(image=plate_img_tk)
                    video_frame_right.image = plate_img_tk
                else:
                    video_frame_right.config(image='')

                update_results(characters)
            
            frame_count += 1
        elif file_path:
            frame = cv2.imread(file_path)
            if frame is not None:
                img_rgb, plate_img, characters = process_frame(frame)
                
                img_tk = ImageTk.PhotoImage(Image.fromarray(img_rgb))
                video_frame_left.config(image=img_tk)
                video_frame_left.image = img_tk

                if show_plate and plate_img is not None:
                    plate_img_tk = ImageTk.PhotoImage(Image.fromarray(plate_img))
                    video_frame_right.config(image=plate_img_tk)
                    video_frame_right.image = plate_img_tk
                else:
                    video_frame_right.config(image='')

                update_results(characters)
            else:
                result_label.config(text="Failed to load image")

def start_frame_processing():
    threading.Thread(target=frame_processing_thread, daemon=True).start()

def stop_detection():
    global cap
    if cap:
        cap.release()
    root.quit()

def upload_image():
    global file_path, is_video, show_plate, frame_count
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
    if file_path:
        is_video = False
        show_plate = True
        frame_count = 0
        result_label.config(text=f"Loaded image: {file_path}")
        start_frame_processing()

def upload_video():
    global cap, file_path, is_video, show_plate, frame_count
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi")])
    if file_path:
        cap = cv2.VideoCapture(file_path)
        is_video = True
        show_plate = True
        frame_count = 0
        result_label.config(text=f"Loaded video: {file_path}")
        start_frame_processing()

def delete_plate(plate_file):
    os.remove(plate_file)
    show_saved_plates()  # Refresh the plate list
    messagebox.showinfo("Info", "Plate image deleted.")

def show_saved_plates():
    plate_window = Toplevel(root)
    plate_window.title("Saved Plates")
    plate_window.geometry("800x600")

    canvas = tk.Canvas(plate_window)
    scrollbar = tk.Scrollbar(plate_window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create table headers
    tk.Label(scrollable_frame, text="Image", borderwidth=2, relief="ridge").grid(row=0, column=0, padx=5, pady=5)
    tk.Label(scrollable_frame, text="Timestamp", borderwidth=2, relief="ridge").grid(row=0, column=1, padx=5, pady=5)
    tk.Label(scrollable_frame, text="Actions", borderwidth=2, relief="ridge").grid(row=0, column=2, padx=5, pady=5)

    row = 1
    for file_name in os.listdir(saved_plate_dir):
        if file_name.endswith(".png"):
            plate_path = os.path.join(saved_plate_dir, file_name)
            plate_img = Image.open(plate_path)
            plate_img.thumbnail((200, 200))
            plate_img_tk = ImageTk.PhotoImage(plate_img)
            
            # Image
            tk.Label(scrollable_frame, image=plate_img_tk, borderwidth=2, relief="ridge").grid(row=row, column=0, padx=5, pady=5)
            # Timestamp
            timestamp = file_name.split('_')[1].split('.')[0]
            tk.Label(scrollable_frame, text=timestamp, borderwidth=2, relief="ridge").grid(row=row, column=1, padx=5, pady=5)
            # Actions
            action_frame = tk.Frame(scrollable_frame)
            tk.Button(action_frame, text="Save", command=lambda p=plate_path: save_plate(p)).pack(side="left", padx=5)
            tk.Button(action_frame, text="Delete", command=lambda p=plate_path: delete_plate(p)).pack(side="left", padx=5)
            action_frame.grid(row=row, column=2, padx=5, pady=5)
            
            # Keep a reference to avoid garbage collection
            scrollable_frame.image_list = scrollable_frame.image_list if hasattr(scrollable_frame, 'image_list') else []
            scrollable_frame.image_list.append(plate_img_tk)

            row += 1

def save_plate(plate_file):
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")], initialfile=os.path.basename(plate_file))
    if save_path:
        os.rename(plate_file, save_path)
        messagebox.showinfo("Info", "Plate image saved successfully.")

root = tk.Tk()
root.title("Real-Time Omani Car Detection Pipeline")
root.configure(bg="black")
root.geometry("1200x800")

logo = Image.open(r"D:\joddb\joddb.png")
logo = logo.resize((200, 100))
logo_image = ImageTk.PhotoImage(logo)
logo_label = tk.Label(root, image=logo_image, bg="black")
logo_label.grid(row=0, column=0, padx=5, pady=5, sticky="nw")

video_frame_left = tk.Label(root, bg="black", fg="white", font=("Courier New", 16), relief="ridge", borderwidth=2)
video_frame_left.grid(row=1, column=0, rowspan=8, columnspan=2, padx=10, pady=10, sticky="nsew")

video_frame_right = tk.Label(root, bg="black", fg="white", font=("Courier New", 16), relief="ridge", borderwidth=2)
video_frame_right.grid(row=1, column=2, rowspan=8, columnspan=2, padx=10, pady=10, sticky="nsew")

controls_frame = tk.Frame(root, bg="black")
controls_frame.grid(row=0, column=2, rowspan=1, columnspan=2, padx=10, pady=10, sticky="ne")

upload_image_button = tk.Button(controls_frame, text="Upload Image", command=upload_image, bg="black", fg="white", font=("Courier New", 14), relief="raised")
upload_image_button.grid(row=0, column=0, padx=5, pady=5)

upload_video_button = tk.Button(controls_frame, text="Upload Video", command=upload_video, bg="black", fg="white", font=("Courier New", 14), relief="raised")
upload_video_button.grid(row=1, column=0, padx=5, pady=5)

show_plates_button = tk.Button(controls_frame, text="Show Saved Plates", command=show_saved_plates, bg="black", fg="white", font=("Courier New", 14), relief="raised")
show_plates_button.grid(row=2, column=0, padx=5, pady=5)

stop_button = tk.Button(controls_frame, text="Stop", command=stop_detection, bg="black", fg="white", font=("Courier New", 14), relief="raised")
stop_button.grid(row=3, column=0, padx=5, pady=5)

result_label = tk.Label(root, text="", bg="black", fg="white", font=("Courier New", 14))
result_label.grid(row=9, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)

root.mainloop()

if cap:
    cap.release()
cv2.destroyAllWindows()
