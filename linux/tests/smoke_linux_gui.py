"""Run with installed dependencies and Xvfb or a real X11 display."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from linux_platform import require_desktop
require_desktop()
import tkinter as tk
import nwn_ai_gui

root = tk.Tk()
app = nwn_ai_gui.NWNAIApp(root)
root.update_idletasks()
root.update()
assert root.winfo_exists()
assert "Backup" in app._settings_frames
app._show_settings_panel("Backup")
root.update_idletasks()
assert app._settings_frames["Backup"].winfo_ismapped()
assert app._backup_ready()
app.on_close()
print('Linux GUI construction smoke test passed (no NWN or AI request).')
