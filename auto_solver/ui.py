import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import pyautogui
import threading
import csv
from config import config
from runner import Runner

# Professional Business Theme Setup
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

PRO_FONT = ("Segoe UI", 13)
HEADER_FONT = ("Segoe UI", 22, "bold")
SUBHEADER_FONT = ("Segoe UI", 14, "bold")

class SelectionOverlay:
    def __init__(self, master, on_selected):
        self.master = master
        self.on_selected = on_selected
        self.master.attributes('-alpha', 0.3)
        self.master.attributes('-fullscreen', True)
        self.master.attributes('-topmost', True)
        self.master.config(cursor="crosshair")
        
        self.canvas = tk.Canvas(self.master, bg="black")
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
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='#1d4ed8', width=3)

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
        self.runner = Runner()
        
        self.root = ctk.CTk()
        self.root.title("Auto Solver Pro")
        # Expanded to fit the live log panel
        self.root.geometry("480x600")
        
        # Connect callbacks from the runner
        self.runner.on_finish_callback = self.on_runner_finished
        self.runner.on_log_callback = self.on_runner_log
        self.runner.on_status_callback = self.on_runner_status
        
        # Header
        self.header = ctk.CTkLabel(self.root, text="Auto Solver Pro", font=HEADER_FONT)
        self.header.pack(pady=(15, 5))

        # Work Mode Selection
        mode_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(mode_frame, text="Work Mode:", font=SUBHEADER_FONT).pack(side="left")
        self.mode_combo = ctk.CTkOptionMenu(mode_frame, values=["Standard", "Google Forms"], 
                                            command=self.on_mode_changed, font=PRO_FONT)
        self.mode_combo.set(config.work_mode)
        self.mode_combo.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # --- Targeting Section (Always Visible) ---
        target_frame = ctk.CTkFrame(self.root, corner_radius=6)
        target_frame.pack(fill="x", pady=10, padx=20)
        
        self.region_lbl = ctk.CTkLabel(target_frame, text="Question Region: Not Set", font=PRO_FONT)
        self.region_lbl.pack(pady=(10, 2))
        ctk.CTkButton(target_frame, text="Select Question Region", command=self.select_region, font=PRO_FONT, corner_radius=4).pack(pady=(0, 10))
        
        self.submit_lbl = ctk.CTkLabel(target_frame, text="Submit Button: Not Set", font=PRO_FONT)
        self.submit_lbl.pack(pady=2)
        ctk.CTkButton(target_frame, text="Select Submit Pos & Color", command=self.select_submit, font=PRO_FONT, corner_radius=4).pack(pady=(0, 10))
        
        # --- Preferences Toggle ---
        self.settings_visible = False
        self.settings_btn = ctk.CTkButton(self.root, text="⚙ Show Preferences", command=self.toggle_settings, 
                                          fg_color="transparent", border_width=1, text_color=("gray20", "gray80"), font=PRO_FONT)
        self.settings_btn.pack(pady=5)
        
        # --- Settings Container (Hidden by default) ---
        self.settings_frame = ctk.CTkScrollableFrame(self.root, corner_radius=6)
        
        # AI Settings
        ctk.CTkLabel(self.settings_frame, text="AI Model Settings", font=SUBHEADER_FONT).pack(pady=(10, 5))
        model_inner = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        model_inner.pack(fill="x", padx=10, pady=5)
        
        self.model_combo = ctk.CTkOptionMenu(model_inner, values=[
            "Gemini 3.7 Flash (High)", "Gemini 3.7 Flash (Medium)", "Gemini 3.6 Flash (High)",
            "Gemini 3.5 Flash (High)", "Gemini 3.1 Pro (High)", "Claude Sonnet 4.6 (Thinking)", "GPT-OSS 120B (Medium)"
        ], dynamic_resizing=False, font=PRO_FONT)
        self.model_combo.set(config.model)
        self.model_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(model_inner, text="View Quota", command=self.check_quota, width=80, font=PRO_FONT).pack(side="right")
        
        # Engine Config
        ctk.CTkLabel(self.settings_frame, text="Engine Configuration", font=SUBHEADER_FONT).pack(pady=(15, 5))
        
        delay_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        delay_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(delay_frame, text="Thinking Delay (sec):", font=PRO_FONT).pack(side="left")
        self.thinking_delay_entry = ctk.CTkEntry(delay_frame, width=80, justify="center", font=PRO_FONT)
        self.thinking_delay_entry.insert(0, str(config.thinking_delay))
        self.thinking_delay_entry.pack(side="right")
        
        scroll_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        scroll_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(scroll_frame, text="Scroll Amount (wheel notches):", font=PRO_FONT).pack(side="left")
        self.scroll_amount_entry = ctk.CTkEntry(scroll_frame, width=80, justify="center", font=PRO_FONT)
        self.scroll_amount_entry.insert(0, str(config.scroll_amount))
        self.scroll_amount_entry.pack(side="right")

        ocr_lang_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        ocr_lang_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(ocr_lang_frame, text="OCR Language (e.g. ukr+rus+eng):", font=PRO_FONT).pack(anchor="w")
        self.ocr_lang_entry = ctk.CTkEntry(ocr_lang_frame, width=200, font=PRO_FONT)
        self.ocr_lang_entry.insert(0, config.ocr_language)
        self.ocr_lang_entry.pack(fill="x", pady=(2, 5))
        
        ocr_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        ocr_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(ocr_frame, text="Tesseract Path:", font=PRO_FONT).pack(anchor="w")
        self.tesseract_entry = ctk.CTkEntry(ocr_frame, width=350, font=PRO_FONT)
        self.tesseract_entry.insert(0, config.tesseract_path)
        self.tesseract_entry.pack(fill="x", pady=(2, 5))
        
        # Theme Toggle
        theme_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(15, 10), padx=10)
        ctk.CTkLabel(theme_frame, text="App Theme:", font=PRO_FONT).pack(side="left")
        self.theme_switch = ctk.CTkSwitch(theme_frame, text="Dark Mode", font=PRO_FONT, command=self.toggle_theme)
        self.theme_switch.select()
        self.theme_switch.pack(side="right")
        
        # --- Live Log Panel (Always visible below target frame/preferences) ---
        self.log_frame = ctk.CTkFrame(self.root, corner_radius=6)
        self.log_frame.pack(fill="both", expand=True, pady=10, padx=20)
        
        self.status_lbl = ctk.CTkLabel(self.log_frame, text="Status: 🛑 Idle", font=SUBHEADER_FONT)
        self.status_lbl.pack(pady=(10, 5), padx=10, anchor="w")
        
        self.log_box = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12), state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # --- Footer ---
        info_lbl = ctk.CTkLabel(self.root, text="F8 = Pause/Resume  |  ESC = Stop", font=PRO_FONT, text_color="gray")
        info_lbl.pack(pady=(10, 5))
        
        self.start_btn = ctk.CTkButton(self.root, text="Start Automation", font=SUBHEADER_FONT, 
                                       height=45, corner_radius=6, command=self.start_automation)
        self.start_btn.pack(pady=(0, 20), padx=40, fill="x")

    def on_runner_log(self, msg: str):
        # Safely interact with Tkinter UI from the background thread
        self.root.after(0, self._append_log, msg)
        
    def _append_log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        
    def on_runner_status(self, status: str):
        # Safely interact with Tkinter UI from the background thread
        self.root.after(0, self._update_status, status)
        
    def _update_status(self, status: str):
        self.status_lbl.configure(text=f"Status: {status}")

    def toggle_settings(self):
        if self.settings_visible:
            self.settings_frame.pack_forget()
            self.settings_btn.configure(text="⚙ Show Preferences")
            self.settings_visible = False
            self.root.geometry("480x600")
        else:
            # Insert settings before log frame so logs remain at bottom
            self.settings_frame.pack(pady=5, padx=20, fill="both", expand=True, before=self.log_frame)
            self.settings_btn.configure(text="⚙ Hide Preferences")
            self.settings_visible = True
            self.root.geometry("480x850")

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def check_quota(self):
        import subprocess
        try:
            result = subprocess.run(["agy", "--print", "/quota"], capture_output=True, text=True, encoding="utf-8")
            if result.returncode == 0:
                self.show_quota_dashboard(result.stdout.strip())
            else:
                messagebox.showerror("Error", f"Failed to get quota:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not check quota: {e}")
            
    def show_quota_dashboard(self, quota_text):
        dashboard = ctk.CTkToplevel(self.root)
        dashboard.title("Quota Dashboard")
        dashboard.geometry("550x400")
        dashboard.attributes('-topmost', True)
        
        ctk.CTkLabel(dashboard, text="Quota Usage & Limits", font=HEADER_FONT).pack(pady=15)
        
        scroll = ctk.CTkScrollableFrame(dashboard, width=500, height=300)
        scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        for line in quota_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) >= 3:
                model = parts[0]
                limit_type = parts[1]
                pct_str = parts[2]
                
                try:
                    pct = float(pct_str.replace('%', '').strip()) / 100.0
                except:
                    pct = 0.0
                    
                frame = ctk.CTkFrame(scroll, corner_radius=5)
                frame.pack(fill="x", pady=5, padx=5)
                
                lbl_text = f"{model} - {limit_type}"
                if len(parts) >= 4:
                    lbl_text += f" (Resets: {parts[3]})"
                    
                ctk.CTkLabel(frame, text=lbl_text, font=PRO_FONT).pack(anchor="w", padx=10, pady=(5,0))
                
                # Progress bar color logic: < 20% red, < 50% yellow, else green
                prog_color = "#10b981" if pct > 0.5 else ("#f59e0b" if pct > 0.2 else "#ef4444")
                
                bar_frame = ctk.CTkFrame(frame, fg_color="transparent")
                bar_frame.pack(fill="x", padx=10, pady=(0,10))
                
                bar = ctk.CTkProgressBar(bar_frame, progress_color=prog_color)
                bar.pack(side="left", fill="x", expand=True, padx=(0,10))
                bar.set(pct)
                
                ctk.CTkLabel(bar_frame, text=pct_str, font=PRO_FONT).pack(side="right")
            else:
                # Fallback for unexpected format
                ctk.CTkLabel(scroll, text=line, font=PRO_FONT).pack(anchor="w", padx=10, pady=2)

    def select_region(self):
        overlay_root = tk.Toplevel(self.root)
        SelectionOverlay(overlay_root, self.on_region_selected)
        
    def on_region_selected(self, region):
        config.question_region = region
        self.region_lbl.configure(text=f"Question Region: {region}")
        
    def select_submit(self):
        messagebox.showinfo("Select Submit", "Move your mouse to the center of the Submit button and press ENTER. We will record the position AND the color of the pixel.")
        
        def wait_for_enter(event):
            pos = pyautogui.position()
            config.submit_button_pos = (pos.x, pos.y)
            color = pyautogui.pixel(pos.x, pos.y)
            config.submit_button_color = color
            self.submit_lbl.configure(text=f"Submit: {pos} | RGB: {color}")
            overlay.destroy()
            self.root.deiconify()
            
        self.root.withdraw()
        overlay = tk.Toplevel()
        overlay.attributes('-alpha', 0.0) # transparent
        overlay.attributes('-fullscreen', True)
        overlay.bind('<Return>', wait_for_enter)
        overlay.focus_force()

    def on_mode_changed(self, new_mode):
        config.work_mode = new_mode
        if new_mode == "Google Forms":
            self.submit_lbl.configure(text="Submit Button: Not needed for Google Forms", text_color="gray")
        else:
            if config.submit_button_pos:
                self.submit_lbl.configure(text=f"Submit: {config.submit_button_pos} | RGB: {config.submit_button_color}", text_color=("gray10", "gray90"))
            else:
                self.submit_lbl.configure(text="Submit Button: Not Set", text_color=("gray10", "gray90"))

    def start_automation(self):
        if not config.question_region:
            messagebox.showerror("Error", "Please select the question region first.")
            return
            
        if config.work_mode == "Standard" and not config.submit_button_pos:
            messagebox.showerror("Error", "Please select the submit position for Standard mode.")
            return
            
        try:
            delay_val = float(self.thinking_delay_entry.get().strip())
            if delay_val < 0:
                raise ValueError()
            config.thinking_delay = delay_val
        except ValueError:
            messagebox.showerror("Error", "Thinking Delay must be a positive number or 0.")
            return
            
        try:
            scroll_val = int(self.scroll_amount_entry.get().strip())
            if scroll_val < 1:
                raise ValueError()
            config.scroll_amount = scroll_val
        except ValueError:
            messagebox.showerror("Error", "Scroll Amount must be a positive integer (minimum 1).")
            return
            
        # Update config with UI values
        config.tesseract_path = self.tesseract_entry.get().strip()
        config.ocr_language = self.ocr_lang_entry.get().strip() or "eng"
        config.model = self.model_combo.get().strip()
        
        if self.runner.is_running:
            self.runner.is_running = False
            self.start_btn.configure(text="Start Automation", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"])
            return
            
        self.start_btn.configure(text="Stop Automation", fg_color="#ef4444", hover_color="#b91c1c")
        
        # Clear log box
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        
        # Run in background thread
        self.runner_thread = threading.Thread(target=self.run_wrapper, daemon=True)
        self.runner_thread.start()
        
    def run_wrapper(self):
        self.runner.run_loop()
        # Once stopped, reset button and status
        self.root.after(0, lambda: self.start_btn.configure(text="Start Automation", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"]))
        self.root.after(0, lambda: self._update_status("🛑 Idle"))

    def run(self):
        self.root.mainloop()
        
    def on_runner_finished(self):
        if config.work_mode == "Google Forms" and self.runner.qa_log:
            self.root.after(0, self.show_qa_log_dashboard)

    def show_qa_log_dashboard(self):
        dashboard = ctk.CTkToplevel(self.root)
        dashboard.title("QA Session Log")
        dashboard.geometry("650x550")
        dashboard.attributes('-topmost', True)
        
        header_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(header_frame, text="Session Q&A Log", font=HEADER_FONT).pack(side="left")
        ctk.CTkButton(header_frame, text="Export to CSV", font=PRO_FONT, command=self.export_report).pack(side="right")
        
        scroll = ctk.CTkScrollableFrame(dashboard)
        scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        for idx, entry in enumerate(self.runner.qa_log, start=1):
            frame = ctk.CTkFrame(scroll, corner_radius=5)
            frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(frame, text=f"Q{idx}: {entry['question']}", font=SUBHEADER_FONT, justify="left", wraplength=550).pack(anchor="w", padx=10, pady=(10, 5))
            ctk.CTkLabel(frame, text=f"A: {entry['answer']}", font=PRO_FONT, text_color="#10b981", justify="left", wraplength=550).pack(anchor="w", padx=10, pady=(0, 10))
            
        ctk.CTkButton(dashboard, text="Close", command=dashboard.destroy, font=PRO_FONT).pack(pady=10)

    def export_report(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")],
            title="Save QA Report"
        )
        if filepath:
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Question No", "Question", "Answer"])
                    for idx, entry in enumerate(self.runner.qa_log, start=1):
                        writer.writerow([idx, entry['question'], entry['answer']])
                messagebox.showinfo("Success", f"Report saved successfully to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report:\n{e}")
