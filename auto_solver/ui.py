import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import pyautogui
import threading
import csv
import time
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
        # We don't hardcode geometry here anymore; let it auto-wrap
        
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
        self.region_btn = ctk.CTkButton(target_frame, text="Select Question Region", command=self.select_region, font=PRO_FONT, corner_radius=4)
        self.region_btn.pack(pady=(0, 10))
        
        self.sequence_container = ctk.CTkFrame(target_frame, fg_color="transparent")
        self.sequence_container.pack(fill="x", pady=2)        
        # --- Native Top Menu Bar ---
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File Menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="View Logs History", command=self.open_history_window)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit Menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(label="Targeting Options", command=self.select_region)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Preferences Menu
        pref_menu = tk.Menu(self.menubar, tearoff=0)
        pref_menu.add_command(label="Settings", command=self.open_settings_window)
        pref_menu.add_separator()
        pref_menu.add_command(label="Toggle Dark/Light Theme", command=self.toggle_theme)
        pref_menu.add_command(label="View Quota", command=self.check_quota)
        self.menubar.add_cascade(label="Preferences", menu=pref_menu)
        
        # --- Live Log Panel (Always visible below target frame/preferences) ---
        self.log_header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.log_header_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        self.status_lbl = ctk.CTkLabel(self.log_header_frame, text="Status: 🛑 Idle", font=PRO_FONT)
        self.status_lbl.pack(side="left")
        
        self.logs_visible = True
        self.log_toggle_btn = ctk.CTkButton(self.log_header_frame, text="▼ Hide Logs", width=80, 
                                            height=24, font=("Segoe UI", 11), 
                                            fg_color="transparent", text_color=("gray30", "gray70"), 
                                            hover_color=("gray85", "gray25"), 
                                            command=self.toggle_logs)
        self.log_toggle_btn.pack(side="right")
        
        self.clear_log_btn = ctk.CTkButton(self.log_header_frame, text="🗑", width=24, 
                                            height=24, font=("Segoe UI", 14), 
                                            fg_color="transparent", text_color=("gray30", "gray70"), 
                                            hover_color=("gray85", "gray25"), 
                                            command=self.clear_logs)
        self.clear_log_btn.pack(side="right", padx=(0, 5))
        
        self.copy_log_btn = ctk.CTkButton(self.log_header_frame, text="📋", width=24, 
                                            height=24, font=("Segoe UI", 14), 
                                            fg_color="transparent", text_color=("gray30", "gray70"), 
                                            hover_color=("gray85", "gray25"), 
                                            command=self.copy_logs)
        self.copy_log_btn.pack(side="right", padx=(0, 5))
        
        self.log_frame = ctk.CTkFrame(self.root, corner_radius=6)
        self.log_frame.pack(fill="both", expand=True, pady=(0, 10), padx=20)
        
        self.log_font_size = 12
        # Set a smaller default height so reqheight is small, allowing the window to shrink
        self.log_box = ctk.CTkTextbox(self.log_frame, font=("Consolas", self.log_font_size), state="disabled", wrap="none", height=100)
        
        self.drag_handle = ctk.CTkFrame(self.log_frame, height=12, cursor="sb_v_double_arrow", fg_color="transparent")
        grip = ctk.CTkFrame(self.drag_handle, height=4, width=50, fg_color=("gray60", "gray40"), corner_radius=2)
        grip.pack(pady=4)
        
        self.drag_handle.bind("<ButtonPress-1>", self.on_drag_start)
        self.drag_handle.bind("<B1-Motion>", self.on_drag_motion)
        grip.bind("<ButtonPress-1>", self.on_drag_start)
        grip.bind("<B1-Motion>", self.on_drag_motion)
        
        self.drag_handle.pack(fill="x", side="bottom")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 0))
        
        # Setup Log Colors
        self.log_box.tag_config("green", foreground="#10b981")
        self.log_box.tag_config("blue", foreground="#3b82f6")
        self.log_box.tag_config("yellow", foreground="#f59e0b")
        self.log_box.tag_config("red", foreground="#ef4444")
        self.log_box.tag_config("gray", foreground="#9ca3af")
        
        # Setup Zoom and Horizontal Scroll
        self.log_box.bind("<Control-MouseWheel>", self.on_log_zoom)
        self.log_box.bind("<Shift-MouseWheel>", self.on_log_hscroll)
        
        # Status Animation State
        self.current_status_text = "Idle"
        self.current_status_start = time.time()
        self.dot_count = 0
        self.is_animating = True
        self._animate_status()
        
        # --- Footer ---
        self.info_lbl = ctk.CTkLabel(self.root, text="F8 = Pause/Resume  |  ESC = Stop", font=PRO_FONT, text_color="gray")
        self.info_lbl.pack(pady=(10, 5))
        
        self.start_btn = ctk.CTkButton(self.root, text="Start Automation", font=SUBHEADER_FONT, 
                                       height=45, corner_radius=6, command=self.start_automation)
        self.start_btn.pack(pady=(0, 10), padx=40, fill="x")
        
        # Open with a spacious default size
        self.root.geometry("480x730")
        
        # Apply initial layout and color theme based on config
        self.on_mode_changed(config.work_mode)
        
        # Lock minimum size to prevent clipping bottom elements (UI + ~100px log box)
        self.root.update_idletasks()
        self.root.wm_minsize(self.root.winfo_reqwidth(), self.root.winfo_reqheight())

    def on_log_zoom(self, event):
        if event.delta > 0:
            self.log_font_size = min(30, self.log_font_size + 1)
        else:
            self.log_font_size = max(6, self.log_font_size - 1)
        self.log_box.configure(font=("Consolas", self.log_font_size))

    def on_log_hscroll(self, event):
        self.log_box._textbox.xview_scroll(int(-1*(event.delta/120)), "units")

    def _animate_status(self):
        if not self.is_animating: return
        
        elapsed = time.time() - self.current_status_start
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        
        # No animation or timer for Idle/Stopped
        if self.current_status_text in ["Idle", "Stopped", "Finished"]:
            self.status_lbl.configure(text=f"Status: {self.current_status_text}")
        else:
            self.status_lbl.configure(text=f"Status: [{elapsed:.1f}s] {self.current_status_text}{dots}")
            
        self.root.after(250, self._animate_status)

    def on_runner_log(self, msg: str, color: str = None):
        self.root.after(0, self._append_log, msg, color)
        
    def _append_log(self, msg: str, color: str = None):
        self.log_box.configure(state="normal")
        if color:
            self.log_box.insert("end", msg + "\n", color)
        else:
            self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        
    def on_runner_status(self, status: str):
        self.root.after(0, self._update_status, status)
        
    def _update_status(self, status: str):
        self.current_status_text = status
        self.current_status_start = time.time()
        self.dot_count = 0
        self.status_lbl.configure(text=f"Status: [0.0s] {self.current_status_text}")

    def on_drag_start(self, event):
        self._drag_start_y = event.y_root
        self._start_height = self.root.winfo_height()
        
    def on_drag_motion(self, event):
        delta = event.y_root - self._drag_start_y
        new_height = max(self.root.wm_minsize()[1], self._start_height + delta)
        self.root.wm_geometry(f"{self.root.winfo_width()}x{new_height}")

    def toggle_logs(self):
        # Relax minimum size so the window is allowed to shrink
        self.root.wm_minsize(self.root.winfo_reqwidth(), 200)
        
        # Capture current exact width and screen position
        w = self.root.winfo_width()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        
        if self.logs_visible:
            # Save ONLY the height before collapsing to prevent teleporting
            self.expanded_height = self.root.winfo_height()
            
            self.log_frame.pack_forget()
            self.log_toggle_btn.configure(text="▶ Show Logs")
            self.logs_visible = False
            
            # Snap to exact required height while strictly keeping width and position
            self.root.update_idletasks()
            req_h = self.root.winfo_reqheight()
            self.root.wm_geometry(f"{w}x{req_h}+{x}+{y}")
            self.root.wm_minsize(self.root.winfo_reqwidth(), req_h)
        else:
            self.log_frame.pack(fill="both", expand=True, pady=(0, 10), padx=20, before=self.info_lbl)
            self.log_toggle_btn.configure(text="▼ Hide Logs")
            self.logs_visible = True
            
            self.root.update_idletasks()
            req_h = self.root.winfo_reqheight()
            
            # Restore previous height, ensuring it's at least the new required minimum
            target_h = getattr(self, 'expanded_height', max(750, req_h))
            target_h = max(req_h, target_h)
            
            self.root.wm_geometry(f"{w}x{target_h}+{x}+{y}")
            self.root.wm_minsize(self.root.winfo_reqwidth(), req_h)

    def copy_logs(self):
        log_text = self.log_box.get("1.0", "end-1c")
        if not log_text.strip():
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(log_text)
        self.copy_log_btn.configure(text="✔", text_color="#10b981")
        self.root.after(1500, lambda: self.copy_log_btn.configure(text="📋", text_color=("gray30", "gray70")))

    def clear_logs(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.clear_log_btn.configure(text="✔", text_color="#10b981")
        self.root.after(1500, lambda: self.clear_log_btn.configure(text="🗑", text_color=("gray30", "gray70")))

    def open_settings_window(self):
        if hasattr(self, "settings_win") and self.settings_win.winfo_exists():
            self.settings_win.focus()
            return
            
        self.settings_win = ctk.CTkToplevel(self.root)
        self.settings_win.title("Preferences")
        self.settings_win.geometry("500x650")
        self.settings_win.attributes('-topmost', True)
        
        frame = ctk.CTkScrollableFrame(self.settings_win, corner_radius=6)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # AI Settings
        ctk.CTkLabel(frame, text="AI Model Settings", font=SUBHEADER_FONT).pack(pady=(10, 5))
        model_inner = ctk.CTkFrame(frame, fg_color="transparent")
        model_inner.pack(fill="x", padx=10, pady=5)
        
        self.model_combo = ctk.CTkOptionMenu(model_inner, values=[
            "Gemini 3.7 Flash (High)", "Gemini 3.7 Flash (Medium)", "Gemini 3.6 Flash (High)",
            "Gemini 3.5 Flash (High)", "Gemini 3.1 Pro (High)", "Claude Sonnet 4.6 (Thinking)", "GPT-OSS 120B (Medium)"
        ], dynamic_resizing=False, font=PRO_FONT)
        self.model_combo.set(config.model)
        self.model_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(model_inner, text="View Quota", command=self.check_quota, width=80, font=PRO_FONT).pack(side="right")
        
        # Engine Config
        ctk.CTkLabel(frame, text="Engine Configuration", font=SUBHEADER_FONT).pack(pady=(15, 5))
        
        delay_frame = ctk.CTkFrame(frame, fg_color="transparent")
        delay_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(delay_frame, text="Thinking Delay (sec):", font=PRO_FONT).pack(side="left")
        self.thinking_delay_entry = ctk.CTkEntry(delay_frame, width=80, justify="center", font=PRO_FONT)
        self.thinking_delay_entry.insert(0, str(config.thinking_delay))
        self.thinking_delay_entry.pack(side="right")
        
        scroll_frame = ctk.CTkFrame(frame, fg_color="transparent")
        scroll_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(scroll_frame, text="Scroll Amount (wheel notches):", font=PRO_FONT).pack(side="left")
        self.scroll_amount_entry = ctk.CTkEntry(scroll_frame, width=80, justify="center", font=PRO_FONT)
        self.scroll_amount_entry.insert(0, str(config.scroll_amount))
        self.scroll_amount_entry.pack(side="right")

        ocr_lang_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ocr_lang_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(ocr_lang_frame, text="OCR Language (e.g. ukr+rus+eng):", font=PRO_FONT).pack(anchor="w")
        self.ocr_lang_entry = ctk.CTkEntry(ocr_lang_frame, width=200, font=PRO_FONT)
        self.ocr_lang_entry.insert(0, config.ocr_language)
        self.ocr_lang_entry.pack(fill="x", pady=(2, 5))
        
        ocr_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ocr_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(ocr_frame, text="Tesseract Path:", font=PRO_FONT).pack(anchor="w")
        self.tesseract_entry = ctk.CTkEntry(ocr_frame, width=350, font=PRO_FONT)
        self.tesseract_entry.insert(0, config.tesseract_path)
        self.tesseract_entry.pack(fill="x", pady=(2, 5))
        
        self.timings_var = ctk.BooleanVar(value=config.show_step_timings)
        self.timings_cb = ctk.CTkCheckBox(frame, text="Show Step Timings in Log", variable=self.timings_var, font=PRO_FONT)
        self.timings_cb.pack(fill="x", pady=(10, 5), padx=10)
        
        self.save_logs_var = ctk.BooleanVar(value=config.save_qa_logs)
        self.save_logs_cb = ctk.CTkCheckBox(frame, text="Enable AI Cleanup & Save Final QA Logs", variable=self.save_logs_var, font=PRO_FONT)
        self.save_logs_cb.pack(fill="x", pady=(5, 15), padx=10)
        
        def save_and_close():
            try:
                delay_val = float(self.thinking_delay_entry.get().strip())
                if delay_val < 0: raise ValueError()
                config.thinking_delay = delay_val
            except ValueError:
                messagebox.showerror("Error", "Thinking Delay must be a positive number or 0.", parent=self.settings_win)
                return
                
            try:
                scroll_val = int(self.scroll_amount_entry.get().strip())
                if scroll_val < 1: raise ValueError()
                config.scroll_amount = scroll_val
            except ValueError:
                messagebox.showerror("Error", "Scroll Amount must be a positive integer (minimum 1).", parent=self.settings_win)
                return
                
            config.tesseract_path = self.tesseract_entry.get().strip()
            config.ocr_language = self.ocr_lang_entry.get().strip() or "eng"
            config.model = self.model_combo.get().strip()
            config.show_step_timings = self.timings_var.get()
            config.save_qa_logs = self.save_logs_var.get()
            
            # Re-render sequence in case anything changed
            self.render_sequence_ui()
            
            self.settings_win.destroy()

        ctk.CTkButton(self.settings_win, text="Save & Close", font=SUBHEADER_FONT, height=40, command=save_and_close).pack(pady=10)

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Light":
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
        
    def snap_window_size(self):
        self.root.update_idletasks()
        req_h = self.root.winfo_reqheight()
        self.root.wm_minsize(self.root.winfo_reqwidth(), req_h)
        if not getattr(self, 'logs_visible', True):
            w = self.root.winfo_width()
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            self.root.wm_geometry(f"{w}x{req_h}+{x}+{y}")

    def render_sequence_ui(self):
        for w in self.sequence_container.winfo_children():
            w.destroy()
            
        fg, hover = self._get_theme_colors()
            
        for i, action in enumerate(config.click_sequence):
            row = ctk.CTkFrame(self.sequence_container, corner_radius=6, border_width=1, border_color=("gray80", "gray20"))
            row.pack(fill="x", padx=10, pady=4)
            
            top_bar = ctk.CTkFrame(row, fg_color="transparent")
            top_bar.pack(fill="x", padx=10, pady=(5, 0))
            
            lbl = ctk.CTkLabel(top_bar, text=action.get('name', f"Action {i+1}"), font=SUBHEADER_FONT)
            lbl.pack(side="left")
            
            def rename_action(idx=i, old_name=action.get('name', f"Action {i+1}")):
                import tkinter.simpledialog
                new_name = tkinter.simpledialog.askstring("Rename Action", "Enter new name for this action:", initialvalue=old_name, parent=self.root)
                if new_name and new_name.strip() != old_name:
                    config.click_sequence[idx]['name'] = new_name.strip()
                    self.render_sequence_ui()
                    
            edit_btn = ctk.CTkButton(top_bar, text="✎", width=24, height=24, font=("Segoe UI", 12), fg_color="transparent", text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"), command=rename_action)
            edit_btn.pack(side="left", padx=(5, 0))
            
            if len(config.click_sequence) > 1:
                del_btn = ctk.CTkButton(top_bar, text="✖", width=24, height=24, font=PRO_FONT, fg_color="#ef4444", hover_color="#b91c1c", command=lambda idx=i: self.delete_action(idx))
                del_btn.pack(side="right")
                
            status_text = f"Pos: {action.get('pos')}" if action.get('pos') else "Not Set"
            if action.get('pos') and action.get('check_color', True) and action.get('color'):
                status_text += f" | RGB: {action.get('color')}"
            elif action.get('pos'):
                status_text += " (No Color Check)"
                
            ctk.CTkLabel(row, text=status_text, font=("Segoe UI", 12), text_color=("gray20", "gray80")).pack(pady=(2, 5))
            
            controls = ctk.CTkFrame(row, fg_color="transparent")
            controls.pack(fill="x", padx=10, pady=(0, 10))
            
            btn = ctk.CTkButton(controls, text="Select Position", font=PRO_FONT, height=28, fg_color=fg, hover_color=hover, command=lambda idx=i: self.select_action_pos(idx))
            btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            chk_var = ctk.BooleanVar(value=action.get('check_color', True))
            def on_check(var_value, idx=i):
                config.click_sequence[idx]['check_color'] = var_value
                self.render_sequence_ui()
                
            chk = ctk.CTkCheckBox(controls, text="Wait for Color", font=("Segoe UI", 11), variable=chk_var, command=lambda v=chk_var, idx=i: on_check(v.get(), idx))
            chk.pack(side="right")
            
        add_btn = ctk.CTkButton(self.sequence_container, text="➕ Add Click Action", width=140, height=28, font=PRO_FONT, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), hover_color=("gray85", "gray25"), command=self.add_action)
        add_btn.pack(pady=(5, 10))
        
        self.snap_window_size()

    def add_action(self):
        new_idx = len(config.click_sequence) + 1
        config.click_sequence.append({"name": f"Action {new_idx}", "pos": None, "color": None, "check_color": True})
        self.render_sequence_ui()
        
    def delete_action(self, idx):
        if 0 <= idx < len(config.click_sequence):
            config.click_sequence.pop(idx)
            self.render_sequence_ui()

    def select_action_pos(self, idx):
        if idx >= len(config.click_sequence): return
        
        messagebox.showinfo("Select Position", f"Move your mouse to the {config.click_sequence[idx]['name']} button and press ENTER. We will record the position.")
        
        def wait_for_enter(event):
            pos = pyautogui.position()
            color = pyautogui.pixel(pos.x, pos.y)
            config.click_sequence[idx]['pos'] = (pos.x, pos.y)
            config.click_sequence[idx]['color'] = color
            overlay.destroy()
            self.root.deiconify()
            self.render_sequence_ui()
            
        self.root.withdraw()
        overlay = tk.Toplevel()
        overlay.attributes('-alpha', 0.0) # transparent
        overlay.attributes('-fullscreen', True)
        overlay.bind('<Return>', wait_for_enter)
        overlay.focus_force()

    def _get_theme_colors(self):
        if config.work_mode == "Google Forms":
            # Light Purple theme for Google Forms
            return ["#a855f7", "#9333ea"], ["#9333ea", "#7e22ce"]
        # Classic Blue theme
        return ["#3B8ED0", "#1F6AA5"], ["#36719F", "#144870"]

    def _apply_theme_colors(self):
        fg, hover = self._get_theme_colors()
        self.mode_combo.configure(fg_color=fg, button_color=fg, button_hover_color=hover)
        self.region_btn.configure(fg_color=fg, hover_color=hover)
        
        # Only update start_btn if it's not currently red (running)
        if not self.runner.is_running:
            self.start_btn.configure(fg_color=fg, hover_color=hover)
            
        # Also re-render sequence UI to apply new colors
        self.render_sequence_ui()

    def on_mode_changed(self, new_mode):
        config.work_mode = new_mode
        self._apply_theme_colors()
        
        if new_mode == "Google Forms":
            # Completely hide the sequence container
            self.sequence_container.pack_forget()
        else:
            # Show the sequence container again
            self.sequence_container.pack(fill="x", pady=2)
                
        # Snap the window dynamically to prevent empty spaces when hiding/showing elements
        self.snap_window_size()

    def start_automation(self):
        if not config.question_region:
            messagebox.showerror("Error", "Please select the question region first.")
            return
            
        if config.work_mode == "Standard":
            for i, act in enumerate(config.click_sequence):
                if not act.get("pos"):
                    messagebox.showerror("Error", f"Please select the position for '{act.get('name', f'Action {i+1}')}'.")
                    return
        
        if self.runner.is_running:
            self.runner.is_running = False
            self.start_btn.configure(text="Start Automation")
            self._apply_theme_colors()
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
        self.root.after(0, lambda: self.start_btn.configure(text="Start Automation"))
        self.root.after(0, self._apply_theme_colors)
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

    def open_history_window(self):
        if hasattr(self, "history_win") and self.history_win.winfo_exists():
            self.history_win.focus()
            return
            
        import history_manager
        
        self.history_win = ctk.CTkToplevel(self.root)
        self.history_win.title("Logs History")
        self.history_win.geometry("700x600")
        self.history_win.attributes('-topmost', True)
        
        header_frame = ctk.CTkFrame(self.history_win, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(header_frame, text="Saved QA Sessions", font=HEADER_FONT).pack(side="left")
        
        controls = ctk.CTkFrame(self.history_win, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=5)
        
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(controls, textvariable=search_var, placeholder_text="Search logs...", width=250, font=PRO_FONT)
        search_entry.pack(side="left")
        
        sort_var = ctk.StringVar(value="Newest First")
        sort_menu = ctk.CTkOptionMenu(controls, variable=sort_var, values=["Newest First", "Oldest First"], width=120, font=PRO_FONT)
        sort_menu.pack(side="right")
        
        list_frame = ctk.CTkScrollableFrame(self.history_win)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        def refresh_list(*args):
            for widget in list_frame.winfo_children():
                widget.destroy()
                
            logs = history_manager.load_history()
            query = search_var.get().lower()
            
            if query:
                logs = [lg for lg in logs if query in lg.get("title", "").lower() or 
                        any(query in pair.get("q", "").lower() or query in pair.get("a", "").lower() for pair in lg.get("qa_pairs", []))]
                        
            if sort_var.get() == "Newest First":
                logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            else:
                logs.sort(key=lambda x: x.get("timestamp", ""))
                
            if not logs:
                ctk.CTkLabel(list_frame, text="No logs found.", font=PRO_FONT, text_color="gray").pack(pady=20)
                return
                
            for log in logs:
                row = ctk.CTkFrame(list_frame, corner_radius=6)
                row.pack(fill="x", pady=5, padx=5)
                
                info_frame = ctk.CTkFrame(row, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                
                title = log.get("title", "Untitled")
                date_str = log.get("timestamp", "")[:16].replace("T", " ")
                pairs_count = len(log.get("qa_pairs", []))
                
                ctk.CTkLabel(info_frame, text=title, font=SUBHEADER_FONT, anchor="w").pack(fill="x")
                ctk.CTkLabel(info_frame, text=f"{date_str}  |  {pairs_count} Q&A pairs", font=("Consolas", 11), text_color="gray", anchor="w").pack(fill="x")
                
                btn_frame = ctk.CTkFrame(row, fg_color="transparent")
                btn_frame.pack(side="right", padx=10, pady=10)
                
                # We need to capture log_id correctly in lambdas
                log_id = log["id"]
                log_title = title
                log_pairs = log.get("qa_pairs", [])
                
                ctk.CTkButton(btn_frame, text="View", width=60, font=PRO_FONT, 
                              command=lambda t=log_title, p=log_pairs: self._view_historical_log(t, p)).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="Rename", width=60, font=PRO_FONT, fg_color="#f59e0b", hover_color="#d97706",
                              command=lambda i=log_id, old=log_title: _rename_log_ui(i, old)).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="Delete", width=60, font=PRO_FONT, fg_color="#ef4444", hover_color="#b91c1c",
                              command=lambda i=log_id: _delete_log_ui(i)).pack(side="left", padx=2)
                              
        def _delete_log_ui(log_id):
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this log?", parent=self.history_win):
                history_manager.delete_log(log_id)
                refresh_list()
                
        def _rename_log_ui(log_id, old_title):
            import tkinter.simpledialog
            new_title = tkinter.simpledialog.askstring("Rename Log", "Enter new title:", initialvalue=old_title, parent=self.history_win)
            if new_title and new_title.strip() != old_title:
                history_manager.rename_log(log_id, new_title.strip())
                refresh_list()
                
        search_var.trace_add("write", refresh_list)
        sort_var.trace_add("write", refresh_list)
        
        refresh_list()
        
    def _view_historical_log(self, title, qa_pairs):
        dashboard = ctk.CTkToplevel(self.history_win)
        dashboard.title("Historical QA Session")
        dashboard.geometry("650x550")
        dashboard.attributes('-topmost', True)
        
        header_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(header_frame, text=title, font=HEADER_FONT).pack(side="left")
        
        scroll = ctk.CTkScrollableFrame(dashboard)
        scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        for idx, entry in enumerate(qa_pairs, start=1):
            frame = ctk.CTkFrame(scroll, corner_radius=5)
            frame.pack(fill="x", pady=5, padx=5)
            
            q = entry.get('q', entry.get('question', ''))
            a = entry.get('a', entry.get('answer', ''))
            
            ctk.CTkLabel(frame, text=f"Q{idx}: {q}", font=SUBHEADER_FONT, justify="left", wraplength=550).pack(anchor="w", padx=10, pady=(10, 5))
            ctk.CTkLabel(frame, text=f"A: {a}", font=PRO_FONT, text_color="#10b981", justify="left", wraplength=550).pack(anchor="w", padx=10, pady=(0, 10))
            
        ctk.CTkButton(dashboard, text="Close", command=dashboard.destroy, font=PRO_FONT).pack(pady=10)
