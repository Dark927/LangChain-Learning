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
    app = AppUI()
    app.run()

if __name__ == "__main__":
    main()
