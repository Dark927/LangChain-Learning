import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
import threading
from config import config
from runner import Runner

class SelectionOverlay:
    def __init__(self, master, on_selected):
        self.master = master
        self.on_selected = on_selected
        self.master.attributes('-alpha', 0.3)
        self.master.attributes('-fullscreen', True)
        self.master.attributes('-topmost', True)
        self.master.config(cursor="crosshair")
        
        self.canvas = tk.Canvas(self.master, bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Escape>", lambda e: self.master.destroy())
        self.master.focus_force()

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=3)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        width = x2 - x1
        height = y2 - y1
        self.on_selected((x1, y1, width, height))
        self.master.destroy()
        
class AppUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto Solver Configuration")
        self.root.geometry("450x450")
        self.root.attributes('-topmost', True)
        
        self.runner = Runner()
        self.runner_thread = None
        
        tk.Label(self.root, text="Auto Solver Setup", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Region and Submit
        self.region_lbl = tk.Label(self.root, text="Question Region: Not Set")
        self.region_lbl.pack(pady=2)
        tk.Button(self.root, text="Select Question Region", command=self.select_region).pack(pady=2)
        
        self.submit_lbl = tk.Label(self.root, text="Submit Button: Not Set")
        self.submit_lbl.pack(pady=2)
        tk.Button(self.root, text="Select Submit Button Pos", command=self.select_submit).pack(pady=2)
        
        # Thinking Delay
        delay_frame = tk.Frame(self.root)
        delay_frame.pack(pady=2)
        tk.Label(delay_frame, text="Thinking Delay (s):").pack(side="left", padx=2)
        self.thinking_delay_entry = tk.Entry(delay_frame, width=10)
        self.thinking_delay_entry.insert(0, str(config.thinking_delay))
        self.thinking_delay_entry.pack(side="left", padx=2)
        
        # Tesseract
        tk.Label(self.root, text="Tesseract Path:").pack(pady=2)
        self.tesseract_entry = tk.Entry(self.root, width=40)
        self.tesseract_entry.insert(0, config.tesseract_path)
        self.tesseract_entry.pack(pady=2)
        
        # Model Selection
        tk.Label(self.root, text="Antigravity Model:").pack(pady=2)
        
        model_frame = tk.Frame(self.root)
        model_frame.pack(pady=2)
        
        self.model_combo = ttk.Combobox(model_frame, width=22, values=[
            "Gemini 3.7 Flash (High)",
            "Gemini 3.7 Flash (Medium)",
            "Gemini 3.6 Flash (High)",
            "Gemini 3.5 Flash (High)",
            "Gemini 3.1 Pro (High)",
            "Claude Sonnet 4.6 (Thinking)",
            "GPT-OSS 120B (Medium)"
        ])
        self.model_combo.set(config.model)
        self.model_combo.pack(side="left", padx=2)
        
        tk.Button(model_frame, text="Check Quota", command=self.check_quota).pack(side="left", padx=2)
        
        # Shortcuts Info
        tk.Label(self.root, text="Shortcuts: F8 = Pause/Resume | ESC = Stop", fg="blue").pack(pady=10)
        
        self.start_btn = tk.Button(self.root, text="Start Automation", command=self.start_automation, bg="green", fg="white", font=("Arial", 12, "bold"))
        self.start_btn.pack(pady=10)
        
    def check_quota(self):
        import subprocess
        try:
            result = subprocess.run(["agy", "--print", "/quota"], capture_output=True, text=True, encoding="utf-8")
            if result.returncode == 0:
                messagebox.showinfo("Antigravity Quota", result.stdout.strip())
            else:
                messagebox.showerror("Error", f"Failed to get quota:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not check quota: {e}")
            
    def select_region(self):
        overlay_root = tk.Toplevel(self.root)
        SelectionOverlay(overlay_root, self.on_region_selected)
        
    def on_region_selected(self, region):
        config.question_region = region
        self.region_lbl.config(text=f"Question Region: {region}")
        
    def select_submit(self):
        messagebox.showinfo("Select Submit", "Move your mouse to the center of the Submit button and press ENTER. We will record the position AND the color of the pixel.")
        
        def wait_for_enter(event):
            pos = pyautogui.position()
            config.submit_button_pos = (pos.x, pos.y)
            color = pyautogui.pixel(pos.x, pos.y)
            config.submit_button_color = color
            self.submit_lbl.config(text=f"Submit: {pos} | RGB: {color}")
            overlay.destroy()
            self.root.deiconify()
            
        self.root.withdraw()
        overlay = tk.Toplevel()
        overlay.attributes('-alpha', 0.0) # transparent
        overlay.attributes('-fullscreen', True)
        overlay.bind('<Return>', wait_for_enter)
        overlay.focus_force()

    def start_automation(self):
        if not config.question_region or not config.submit_button_pos:
            messagebox.showerror("Error", "Please select both the question region and submit position first.")
            return
            
        try:
            delay_val = float(self.thinking_delay_entry.get().strip())
            if delay_val < 0:
                raise ValueError()
            config.thinking_delay = delay_val
        except ValueError:
            messagebox.showerror("Error", "Thinking Delay must be a positive number or 0.")
            return
            
        # Update config with UI values
        config.tesseract_path = self.tesseract_entry.get().strip()
        config.model = self.model_combo.get().strip()
        
        if self.runner.is_running:
            self.runner.is_running = False
            self.start_btn.config(text="Start Automation", bg="green")
            return
            
        self.start_btn.config(text="Stop Automation", bg="red")
        
        # Run in background thread
        self.runner_thread = threading.Thread(target=self.run_wrapper, daemon=True)
        self.runner_thread.start()
        
    def run_wrapper(self):
        self.runner.run_loop()
        # Once stopped, reset button
        self.root.after(0, lambda: self.start_btn.config(text="Start Automation", bg="green"))

    def run(self):
        self.root.mainloop()
