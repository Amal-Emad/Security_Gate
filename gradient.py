import tkinter as tk

def gradient(canvas, gradient_color):
    for i in range(800):
        color = f'#{int(i * 0.5):02x}{int(i * 0.5):02x}{int(i * 0.5):02x}'
        canvas.create_line(0, i, 1200, i, fill=color)
    canvas.create_line(0, 0, 0, 800, fill=gradient_color)
