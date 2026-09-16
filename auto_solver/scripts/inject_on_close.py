import codecs

with open('src/ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        # Lock minimum size to prevent clipping bottom elements (UI + ~100px log box)
        self.root.update_idletasks()
        self.root.wm_minsize(self.root.winfo_reqwidth(), self.root.winfo_reqheight())"""

replacement = """        # Lock minimum size to prevent clipping bottom elements (UI + ~100px log box)
        self.root.update_idletasks()
        self.root.wm_minsize(self.root.winfo_reqwidth(), self.root.winfo_reqheight())
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        \"\"\"Save settings and completely shut down the application.\"\"\"
        from config import config
        config.save_to_file()
        if hasattr(self, 'runner') and self.runner and self.runner.running:
            self.stop_automation()
        self.root.quit()
        self.root.destroy()"""

if target in content:
    with open('src/ui.py', 'w', encoding='utf-8') as f:
        f.write(content.replace(target, replacement))
    print("Replaced!")
else:
    print("Target not found.")
