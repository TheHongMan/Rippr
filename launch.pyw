import subprocess
import threading
import time
import webbrowser
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:5000")

threading.Thread(target=open_browser, daemon=True).start()

subprocess.run(
    [sys.executable, "app.py"],
    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
)
