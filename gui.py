# auto-py-to-exe

import threading
import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfile
import cv2, numpy as np, matplotlib.pyplot as plt
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from skimage.metrics import structural_similarity

# Globals
comparison_figure = None
diff_image = None
frames = None
processing_thread = None
is_processing = False
filename_one = None
filename_two = None
next_slot = 0

image_files = [
            ("PNG File", "*.png"),
            ("JPG File", "*.jpg"),
            ("Gif File", "*.gif")
        ]

animated_files = [("Gif File", "*.gif")]

def process_images():
    global is_processing, comparison_figure

    try:
        # Heavy work starts
        before = cv2.imread(filename_one)
        after = cv2.imread(filename_two)

        if before.shape != after.shape:
            status_label.config(text="Input images must have the same dimensions.")
            return

        before_original = before.copy()
        after_original = after.copy()

        # Convert + compute SSIM
        before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
        (score, diff) = structural_similarity(before_gray, after_gray, full=True)
        diff = (diff * 255).astype("uint8")

        # Find contours
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]

        mask = np.zeros(before.shape, dtype='uint8')
        diff_box = cv2.merge([diff, diff, diff])
        filled_after = after.copy()

        for c in contours:
            if cv2.contourArea(c) > 40:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(before, (x, y), (x + w, y + h), (36, 255, 12), 2)
                cv2.rectangle(after, (x, y), (x + w, y + h), (36, 255, 12), 2)
                cv2.rectangle(diff_box, (x, y), (x + w, y + h), (36, 255, 12), 2)
                cv2.drawContours(mask, [c], 0, (255,255,255), -1)
                cv2.drawContours(filled_after, [c], 0, (0,255,0), -1)

        # Prepare display data
        #before_rgb = cv2.cvtColor(before, cv2.COLOR_BGR2RGB)
        before_original = cv2.cvtColor(before_original, cv2.COLOR_BGR2RGB)
        after_original = cv2.cvtColor(after_original, cv2.COLOR_BGR2RGB)
        after_rgb = cv2.cvtColor(after, cv2.COLOR_BGR2RGB)
        diff_box_rgb = cv2.cvtColor(diff_box, cv2.COLOR_BGR2RGB)
        mask_rgb = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
        filled_after_rgb = cv2.cvtColor(filled_after, cv2.COLOR_BGR2RGB)

        images = [before_original, after_original, after_rgb, diff_box_rgb, mask_rgb, filled_after_rgb]
        titles = ['Before', 'After', 'Diff', 'Diff + Boxes', 'Mask', 'Filled After']
        #titles = ['Before', 'After', "Diff + Boxes"]

        # Schedule GUI update back on main thread
        root.after(0, lambda: make_figure(images, titles, score))
    finally:
        # Mark the thread as finished
        status_label.config(text="Complete")
        btn_save.config(state="normal", cursor="hand2")
        is_processing = False

def make_figure(images, titles, score):
    global comparison_figure, diff_image, frames

    # Create Animated Gif
    frames = []

    for image in images[:3]:
        pil_image = Image.fromarray(image)
        frames.append(pil_image)

    # Create Figure
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(8, 6))
    for ax, img, title in zip(axes.flat, images, titles):
        ax.imshow(img if len(img.shape) == 3 else img, cmap='gray')
        #ax.set_title(title)
        ax.axis('off')
    plt.tight_layout()

    comparison_figure = fig  # store globally

    # Create Individual Image
    diff_image = cv2.cvtColor(images[2], cv2.COLOR_BGR2RGB)

    # Draw Individual Image to Canvas
    pil_image = Image.fromarray(images[2])
    pil_image = pil_image.resize((500,300), Image.Resampling.LANCZOS)
    imgtk = ImageTk.PhotoImage(pil_image)

    # clear previous images before adding new one
    canvas.delete("all")

    # draw centered in the canvas
    canvas.create_image(canvas.winfo_width()//2,
                        canvas.winfo_height()//2,
                        image=imgtk,
                        anchor=tk.CENTER
    )
    canvas.image = imgtk  # 🔹 keep a reference tied to the widget

def start_comparison(event=None):
    global processing_thread, is_processing, filename_one, filename_two

    if not filename_one or not filename_two:
        status_label.config(text="Missing one or more input files.")
        return

    if is_processing:
        print("Already running — ignoring duplicate request.")
        return

    is_processing = True
    #btn_compare.config(state="disabled")
    status_label.config(text="Processing...")

    # Create new clean thread
    processing_thread = threading.Thread(target=process_images, daemon=True)
    processing_thread.start()

def save_image(event=None):
    global comparison_figure, diff_image, filename_one, filename_two
    
    if not comparison_figure:
        return

    if radio_var.get() == 0 or radio_var.get() == 1:
        file_path = asksaveasfile(filetypes=image_files, defaultextension="*.png", title="Save as")
    else:
        file_path = asksaveasfile(filetypes=animated_files, defaultextension="*.gif", title="Save as")

    
    if file_path:
        if radio_var.get() == 0:
            comparison_figure.savefig(file_path.name, dpi=1000)
        elif radio_var.get() == 1:
            cv2.imwrite(file_path.name, diff_image)
        else:
            frames[0].save(file_path.name, save_all=True, append_images=frames[1:], duration=900, loop=0)
            
        status_label.config(text=f"Saved at: {file_path.name}")

def choosing_file(event=None, slot=None):
    global filename_one, filename_two, next_slot

    # If slot not provided, use and flip the next_slot
    if slot is None:
        slot = next_slot
        next_slot = 1 - next_slot # toggles between 0 and 1

    # Choose which lable and variable to use based on slot
    label = filename_one_label if slot == 0 else filename_two_label

    # Clear current content
    label.config(state="normal")
    label.delete("1.0", tk.END)

    # Ask for file
    filename = askopenfilename()

    # Display the filename centered
    label.tag_configure("center", justify="center")
    label.insert(tk.END, filename)
    label.tag_add("center", "1.0", "end")

    label.config(state="disabled")

    # Save to the correct global variable
    if slot == 0:
        filename_one = filename
    else:
        filename_two = filename

def reset_window(event=None):
    global comparison_figure, diff_image, frames, processing_thread, is_processing, filename_one, filename_two

    # Reset global values
    comparison_figure = None
    diff_image = None
    frames = None
    processing_thread = None
    is_processing = False
    filename_one = None
    filename_two = None

    # Remove file locations in both boxes
    filename_one_label.config(state="normal")
    filename_one_label.delete("1.0", tk.END)

    filename_two_label.config(state="normal")
    filename_two_label.delete("1.0", tk.END)

    filename_one_label.config(state="disabled", bg="white")
    filename_two_label.config(state="disabled", bg="white")

    # Reset label to the Ready status
    status_label.config(text="Ready")

    # Unlock compare Images button
    btn_compare.config(state="normal")

    # clear previous images before adding new one
    canvas.delete("all")

    # Lock Save Button
    btn_save.config(state="disabled")

    # Reset radio button
    radio_var.set(0)

def exit_app(event=None):
    # Closes the main Tkinter window
    root.destroy()

# Tkinter GUI
root = tk.Tk()
root.title("Thread-Safe Image Comparison")
root.geometry('600x700')
root.resizable(width=False, height=False)

# Setting up Menu
menu = tk.Menu()
root.config(menu=menu)

filemenu = tk.Menu(menu, tearoff=False)
helpmenu = tk.Menu(menu, tearoff=False)

menu.add_cascade(label="File", menu=filemenu)
menu.add_cascade(label="Help", menu=helpmenu)

filemenu.add_command(label="New", command=lambda: reset_window(), accelerator="Ctrl+R")
filemenu.add_command(label="Open", command=lambda: choosing_file(), accelerator="Ctrl+O")
filemenu.add_command(label="Save", command=lambda: save_image(), accelerator="Ctrl+S")
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit, accelerator="Ctrl+Shift+W")

helpmenu.add_cascade(label="About")

# File Selection Grid Frame
file_selection_frame = tk.Frame(root)

# lambda creates anonymous functions that can be passed argurmnets to widget commands or event handlers
btn_filename_one = tk.Button(file_selection_frame, text="Picture One Location", command=lambda: choosing_file(slot=0), cursor="hand2", font=("Arial", 12))
btn_filename_two = tk.Button(file_selection_frame, text="Picture Two Location", command=lambda: choosing_file(slot=1), cursor="hand2", font=("Arial", 12))

filename_one_label = tk.Text(file_selection_frame, height=1.5, width=35, font=("Arial", 12), state="disabled", wrap="word")
filename_two_label = tk.Text(file_selection_frame, height=1.5, width=35, font=("Arial", 12), state="disabled", wrap="word")

btn_filename_one.grid(row=0, column=1, padx=5, pady=2)
filename_one_label.grid(row=0, column=2, padx=5, pady=5)
btn_filename_two.grid(row=1, column=1, padx=5, pady=2)
filename_two_label.grid(row=1, column=2, padx=5, pady=5)

file_selection_frame.pack(pady=10)

# Status Label
status_label = tk.Label(root, text="Ready", font=("Arial", 12))
status_label.pack(pady=5)

# Compare Button
btn_compare = tk.Button(root, text="Compare Images", command=lambda: start_comparison(), font=("Arial", 12), cursor="hand2")
btn_compare.pack(pady=10)

# Canvas
canvas = tk.Canvas(root, width=500, height=300)
canvas.pack(pady=10)

# Radio buttons frame
radio_button_frame = tk.Frame(root)

save_options = ["Comparison Figure", "Individual Image", "Animated Gif"]
radio_var = tk.IntVar()

for index in range(len(save_options)):
    tk.Radiobutton(radio_button_frame,font=("Arial", 12), text=save_options[index], variable=radio_var, value=index, padx=5).pack(side=tk.LEFT, pady=20)

radio_button_frame.pack()

# Save Selection Grid Frame
save_selection_frame = tk.Frame(root)

btn_save = tk.Button(save_selection_frame, text="Save", command=lambda: save_image(), font=("Arial", 12), state="disabled")
btn_reset = tk.Button(save_selection_frame, text="Reset", command=lambda: reset_window(), font=("Arial", 12), cursor="hand2")

btn_save.grid(row=0, column=1, padx= 5, pady=2)
btn_reset.grid(row=0, column=2, padx=5, pady=2)

save_selection_frame.pack(pady=10)

# Bindings
root.bind("<Control-r>", lambda event: reset_window(event))                 # Bind Ctrl+r (Reset Window)
root.bind("<Control-Key-1>", lambda event: choosing_file(event, slot=0))    # Bind Ctrl+1 (Choose File One)
root.bind("<Control-Key-2>", lambda event: choosing_file(event, slot=1))    # Bind Ctrl+2 (Choose File Two)
root.bind("<Control-o>", lambda event: choosing_file(event))                # Bind Ctrl+o (Choose file)
root.bind("<Control-space>", lambda event: start_comparison(event))         # Bind Ctrl+Space (Start Processing)
root.bind("<Control-s>", lambda event: save_image(event))                   # Bind Ctrl+s (Save Image)
root.bind("<Control-Shift-KeyPress-W>", lambda event: exit_app(event))      # Bind Ctrl+Shift+W (exit application)


root.mainloop()
