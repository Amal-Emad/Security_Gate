import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
from datetime import datetime
import os


saved_plate_dir = r'D:\oman_car_plates\saved_plates'


root = tk.Tk()
root.title("Main Window")
root.geometry("1200x800")
root.configure(bg="#1E201E")


cap = cv2.VideoCapture(0)

def show_frame():
    ret, frame = cap.read()
    if ret:
      
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(cv2image)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        video_label.config(image=img_tk)
        video_label.image = img_tk
        
    root.after(10, show_frame)

def capture_image():
    ret, frame = cap.read()
    if ret:
       
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_filename = os.path.join(saved_plate_dir, f"capture_{timestamp}.png")
       
        cv2.imwrite(img_filename, frame)
       
        messagebox.showinfo("Capture", f"Image saved as {img_filename}")
        
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img_tk = ImageTk.PhotoImage(image=img_pil)
        captured_image_label.config(image=img_tk)
        captured_image_label.image = img_tk


video_label = tk.Label(root)
video_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

captured_image_label = tk.Label(root)
captured_image_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")


capture_button = tk.Button(root, text="Capture Image", command=capture_image, bg="#A0937D", fg="black", font=("Courier New", 12, "bold"), relief="raised", borderwidth=2)
capture_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

show_frame()


root.protocol("WM_DELETE_WINDOW", lambda: (cap.release(), root.destroy()))


root.mainloop()
