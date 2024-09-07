import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os
from datetime import datetime
from model import PipelineModel
import threading
import queue


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

plate_saved = False
frame_queue = queue.Queue()

# Function to resize the image to fit the frame
def resize_image_to_fit(frame_width, frame_height, image):
    img_width, img_height = image.size
    scale_width = frame_width / img_width
    scale_height = frame_height / img_height
    scale = min(scale_width, scale_height)
    
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    
    return image.resize((new_width, new_height), Image.ANTIALIAS)

# Function to process the frame
def process_frame(frame):
    global plate_saved
    car_boxes, plates, characters = pipeline.detect(frame)
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    for box in car_boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(img_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    plate_img = None
    if plates and not plate_saved:
        px1, py1, px2, py2, plate_crop = plates[0]
        cv2.rectangle(img_rgb, (px1, py1), (px2, py2), (255, 0, 0), 2)
        plate_img = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2RGB)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plate_filename = os.path.join(saved_plate_dir, f"plate_{timestamp}.png")
        cv2.imwrite(plate_filename, cv2.cvtColor(plate_crop, cv2.COLOR_RGB2BGR))
        plate_saved = True

    img_pil = Image.fromarray(img_rgb)
    return img_pil, plate_img, characters

# Function to update the results
def update_results(characters):
    result_text = "Detection Results:\n"
    filtered_labels = []
    
    valid_labels = set(map(str, range(10)))
    valid_labels.update(chr(c) for c in range(65, 91))
    
    if characters:
        for _, _, _, _, label in characters:
            if label in valid_labels:
                filtered_labels.append(label)
    
    if filtered_labels:
        result_text += " ".join(filtered_labels)
    else:
        result_text += "No valid characters detected."
    
    result_label.config(text=result_text)

# Thread function to process the frame
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
                frame_queue.put(frame)
            
            frame_count += 1
        elif file_path:
            frame = cv2.imread(file_path)
            if frame is not None:
                frame_queue.put(frame)
            else:
                result_label.config(text="Failed to load image")
        
        cv2.waitKey(10)

# Function to process the queue and update the UI
def process_queue():
    while not frame_queue.empty():
        frame = frame_queue.get()
        img_pil, plate_img, characters = process_frame(frame)
        
        img_width, img_height = video_frame_left.winfo_width(), video_frame_left.winfo_height()
        img_resized = resize_image_to_fit(img_width, img_height, img_pil)
        img_tk = ImageTk.PhotoImage(img_resized)
        video_frame_left.config(image=img_tk)
        video_frame_left.image = img_tk
        
        if show_plate and plate_img is not None:
            plate_img_pil = Image.fromarray(plate_img)
            plate_img_width, plate_img_height = video_frame_right.winfo_width(), video_frame_right.winfo_height()
            plate_img_resized = resize_image_to_fit(plate_img_width, plate_img_height, plate_img_pil)
            plate_img_tk = ImageTk.PhotoImage(plate_img_resized)
            video_frame_right.config(image=plate_img_tk)
            video_frame_right.image = plate_img_tk
        else:
            video_frame_right.config(image='')
        
        update_results(characters)
    
    root.update_idletasks()
    root.after(100, process_queue)

# Function to start frame processing
def start_frame_processing():
    global frame_queue
    frame_queue.queue.clear()
    threading.Thread(target=frame_processing_thread, daemon=True).start()
    root.after(100, process_queue)

# Function to clear previous data
def clear_previous_data():
    global cap, file_path, is_video, plate_saved
    if cap:
        cap.release()
        cap = None
    file_path = None
    is_video = False
    plate_saved = False
    video_frame_left.config(image='')
    video_frame_right.config(image='')
    result_label.config(text='')
    global frame_queue
    frame_queue.queue.clear()

# Function to upload image
def upload_image():
    clear_previous_data()
    global file_path, is_video, show_plate, frame_count
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
    if file_path:
        is_video = False
        show_plate = True
        frame_count = 0
        result_label.config(text=f"Loaded image: {file_path}")
        start_frame_processing()

def open_capture_window():
    capture_window = tk.Toplevel(root)
    capture_window.title("Capture")
    capture_window.geometry("800x600")
    
    cap = cv2.VideoCapture(0)
    
    def show_frame():
        ret, frame = cap.read()
        if ret:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(cv2image)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            video_frame_left.config(image=img_tk)
            video_frame_left.image = img_tk
            
        capture_window.after(10, show_frame)
    
    def capture_image():
        ret, frame = cap.read()
        if ret:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_filename = os.path.join(saved_plate_dir, f"capture_{timestamp}.png")
            cv2.imwrite(img_filename, frame)
            messagebox.showinfo("Capture", f"Image saved as {img_filename}")
    
    capture_button = tk.Button(capture_window, text="Capture Image", command=capture_image, bg="#A0937D", fg="black", font=("Courier New", 12, "bold"))
    capture_button.pack(side=tk.BOTTOM, pady=10)
    
    capture_window.after(10, show_frame)
# Function to show saved plates
def show_saved_plates():
    import table
    table.show_saved_plates(root)

# Function to stop detection
def stop_detection():
    global cap, is_video
    if cap:
        cap.release()
        cap = None
    is_video = False
    clear_previous_data()
    result_label.config(text="Detection stopped.")

# Tkinter 
root = tk.Tk()
root.title("Car Detection Pipeline")
root.configure(bg="#1E201E")
root.geometry("1200x800")


logo = Image.open(r"D:\oman_car_plates\joddb.png")
logo = logo.resize((200, 100))
logo_image = ImageTk.PhotoImage(logo)
logo_label = tk.Label(root, image=logo_image, bg="#1E201E", highlightbackground="beige",relief="groove", highlightcolor="beige", highlightthickness=1.5)
logo_label.grid(row=0, column=0, padx=10, pady=5, sticky="nw")

title_label = tk.Label(root, text="Security Gate", bg="#1E201E", fg="beige", font=("Courier New", 20, "bold"),relief="groove", highlightbackground="black", highlightcolor="black", highlightthickness=1.5)
title_label.grid(row=0, column=0, columnspan=2, padx=5, pady=35, sticky="n")


video_frame_left = tk.Label(root, text="VEHICLE", bg="#1E201E", fg="white", font=("Courier New", 16, "bold"), relief="groove", borderwidth=1, bd=2, highlightbackground="beige", highlightcolor="black", highlightthickness=4)
video_frame_left.grid(row=1, column=0, rowspan=8, padx=8, pady=8, sticky="nsew")


video_frame_right = tk.Label(root, text="PLATE", bg="#1E201E", fg="white", font=("Courier New", 16, "bold"),relief="groove", borderwidth=1, bd=2, highlightbackground="beige", highlightcolor="black", highlightthickness=4)
video_frame_right.grid(row=1, column=1, rowspan=8, padx=8, pady=8, sticky="nsew")


button_font = ("Courier New", 10, "bold") 
button_padx = 10  
button_pady = 5  
button_width = 20 


upload_image_button = tk.Button(
    root, text="Upload Image", command=upload_image, bg="#1E201E", fg="beige",
    font=button_font, relief="raised", borderwidth=2, width=button_width
)
upload_image_button.grid(
    row=9, column=0, padx=button_padx, pady=button_pady, sticky="nsew"
)

capture_button = tk.Button(
    root, text="Capture", command=open_capture_window, bg="#1E201E", fg="beige",
    font=button_font, relief="raised", borderwidth=2, width=button_width
)
capture_button.grid(
    row=9, column=1, padx=button_padx, pady=button_pady, sticky="nsew"
)


show_saved_plates_button = tk.Button(
    root, text="Show Saved Plates", command=show_saved_plates, bg="#1E201E", fg="beige",
    font=button_font, relief="raised", borderwidth=2, width=button_width
)
show_saved_plates_button.grid(
    row=10, column=0, padx=button_padx, pady=button_pady, sticky="nsew"
)


stop_detection_button = tk.Button(
    root, text="Stop Detection", command=stop_detection, bg="#1E201E", fg="beige",
    font=button_font, relief="raised", borderwidth=2, width=button_width
)
stop_detection_button.grid(
    row=10, column=1, padx=button_padx, pady=button_pady, sticky="nsew"
)


root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)


result_label = tk.Label(root, text="MADE WITH LOVE  ❤️BY AMAL ALKRAIMEEN", bg="#1E201E", fg="beige", font=("Courier New", 12, "bold"))
result_label.grid(row=11, column=0, columnspan=2, padx=10, pady=15, sticky="ew")



root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)


root.mainloop()
