import sys
from ui import AppUI

def setup_environment():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

def main():
    setup_environment()
    print("Initializing Auto Solver...")
    
    # 1. Check and perform Antigravity CLI Auth / Install
    from auth_manager import AuthManager
    AuthManager.check_and_setup()
    
    # 2. Run Main UI Loop
    while True:
        app = AppUI()
        app.run()
        if not getattr(app, 'wants_restart', False):
            break

if __name__ == "__main__":
    main()
