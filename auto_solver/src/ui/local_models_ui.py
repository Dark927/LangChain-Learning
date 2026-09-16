import tkinter as tk
import customtkinter as ctk
import os
from agents.local_models import RECOMMENDED_MODELS, get_installed_models, delete_model, download_model_async

class LocalModelsWindow:
    def __init__(self, parent, on_update_callback=None):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Local Models Manager (Offline)")
        self.window.geometry("700x500")
        self.window.grab_set()
        
        self.on_update_callback = on_update_callback
        
        # Header
        header = ctk.CTkLabel(self.window, text="Offline Local Models Manager", font=("Segoe UI", 20, "bold"))
        header.pack(pady=(20, 5))
        desc = ctk.CTkLabel(self.window, text="Download uncensored models that run 100% locally on your machine.\nNo internet required after download. No limits.", text_color="gray")
        desc.pack(pady=(0, 20))
        
        self.scroll = ctk.CTkScrollableFrame(self.window)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        bottom_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(bottom_frame, text="Open Models Folder", command=self.open_folder, fg_color="gray", hover_color="#4b5563").pack(side="right")
        
        self.refresh_list()
        
    def open_folder(self):
        import os
        from agents.local_models import get_models_dir
        os.startfile(get_models_dir())
        
    def refresh_list(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
            
        installed_files = [m["filename"] for m in get_installed_models()]
        
        for idx, model in enumerate(RECOMMENDED_MODELS):
            frame = ctk.CTkFrame(self.scroll, corner_radius=6)
            frame.pack(fill="x", pady=5, padx=5)
            
            action_frame = ctk.CTkFrame(frame, fg_color="transparent")
            action_frame.pack(side="right", padx=10, pady=10)

            info_frame = ctk.CTkFrame(frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(info_frame, text=model["name"], font=("Segoe UI", 16, "bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Size: ~{model['size_gb']} GB  |  {model['filename']}", text_color="gray", font=("Segoe UI", 12)).pack(anchor="w")
            
            if model["filename"] in installed_files:
                btn = ctk.CTkButton(action_frame, text="Delete", fg_color="#ef4444", hover_color="#b91c1c", width=80,
                                    command=lambda m=model: self.on_delete(m["filename"]))
                btn.pack(side="right")
                ctk.CTkLabel(action_frame, text="✓ Installed", text_color="#10b981", font=("Segoe UI", 14, "bold")).pack(side="right", padx=10)
            else:
                progress_bar = ctk.CTkProgressBar(action_frame, width=150)
                progress_bar.set(0)
                # Hidden initially
                
                btn = ctk.CTkButton(action_frame, text="Download", width=100)
                btn.configure(command=lambda m=model, b=btn, p=progress_bar: self.on_download(m, b, p))
                btn.pack(side="right")
                
    def on_delete(self, filename):
        delete_model(filename)
        self.refresh_list()
        if self.on_update_callback:
            self.on_update_callback()
            
    def on_download(self, model, btn, progress_bar):
        btn.configure(state="disabled", text="Starting...")
        progress_bar.pack(side="right", padx=10)
        progress_bar.set(0)
        
        def on_progress(percent):
            # Update UI on main thread safely
            self.window.after(0, lambda: progress_bar.set(percent))
            self.window.after(0, lambda: btn.configure(text=f"{int(percent*100)}%"))
            
        def on_complete():
            self.window.after(0, self.refresh_list)
            if self.on_update_callback:
                self.window.after(0, self.on_update_callback)
                
        def on_error(err):
            self.window.after(0, lambda: btn.configure(state="normal", text="Error (Retry)"))
            self.window.after(0, progress_bar.pack_forget)
            print(f"Download Error: {err}")
            
        download_model_async(model["url"], model["filename"], on_progress, on_complete, on_error)
