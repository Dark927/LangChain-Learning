import os
import sys
import subprocess
import threading
import urllib.request
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Placeholder URL - replace with the actual Antigravity CLI download URL or pip install command
AGY_DOWNLOAD_URL = "https://example.com/agy-latest.zip" 

class AuthManager:
    @staticmethod
    def check_and_setup():
        # Create a hidden root window just for message boxes before main UI starts
        temp_root = ctk.CTk()
        temp_root.withdraw()
        
        if not AuthManager.is_agy_installed():
            response = messagebox.askyesno(
                "Setup Required", 
                "Antigravity CLI (agy) was not found on your system.\n\nWould you like to download and install it now?", 
                parent=temp_root
            )
            if response:
                AuthManager.download_agy(temp_root)
            else:
                messagebox.showwarning("Warning", "Auto Solver Pro requires Antigravity CLI to function. Exiting.", parent=temp_root)
                sys.exit(0)
        
        if not AuthManager.is_authenticated():
            messagebox.showinfo(
                "Authentication Required", 
                "You are not currently authorized to Antigravity.\n\nA terminal window will now open. Please complete the login process, and then return to the solver.", 
                parent=temp_root
            )
            AuthManager.perform_auth()
            
        temp_root.destroy()

    @staticmethod
    def is_agy_installed():
        try:
            subprocess.run(["agy", "--help"], capture_output=True, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    @staticmethod
    def download_agy(root):
        dl_win = ctk.CTkToplevel(root)
        dl_win.title("Downloading Antigravity CLI")
        dl_win.geometry("400x150")
        dl_win.attributes('-topmost', True)
        
        lbl = ctk.CTkLabel(dl_win, text="Setting up Antigravity CLI...", font=("Roboto", 16, "bold"))
        lbl.pack(pady=(20, 10))
        
        progress = ctk.CTkProgressBar(dl_win)
        progress.pack(fill="x", padx=20)
        progress.set(0)
        progress.start()
        
        def download_task():
            try:
                # TODO: Implement actual download logic here.
                # E.g., urllib.request.urlretrieve(AGY_DOWNLOAD_URL, "agy.zip")
                # unzip to a local folder, and add to PATH.
                
                # For now, we simulate a delay for the UI demonstration
                import time
                time.sleep(2)
                
                messagebox.showinfo(
                    "Setup Information", 
                    "Please insert your specific AGY download/installation logic in auth_manager.py.\n(e.g. Downloading zip or running pip install)", 
                    parent=dl_win
                )
            except Exception as e:
                messagebox.showerror("Error", f"Setup failed: {e}", parent=dl_win)
            finally:
                progress.stop()
                dl_win.destroy()
                
        threading.Thread(target=download_task, daemon=True).start()
        root.wait_window(dl_win)

    @staticmethod
    def is_authenticated():
        try:
            # We run a basic command that communicates with the server.
            # If the user is unauthenticated, it will typically return an auth error.
            res = subprocess.run(["agy", "agent"], capture_output=True, text=True)
            
            output = (res.stdout + res.stderr).lower()
            if "unauthorized" in output or "login" in output or "not logged in" in output:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def perform_auth():
        if sys.platform == "win32":
            # Opens a new interactive console running agy so the user can log in
            # We pause afterwards so they can read any success/error messages before it closes
            instruction = "echo === Antigravity Setup === & echo. & echo IMPORTANT: When your browser gives you an authentication code, & echo please PASTE IT DIRECTLY INTO THIS BLACK TERMINAL WINDOW and press ENTER! & echo. & agy & echo. & echo Press any key to return to Solver... & pause"
            subprocess.run(["start", "cmd.exe", "/c", instruction], shell=True)
