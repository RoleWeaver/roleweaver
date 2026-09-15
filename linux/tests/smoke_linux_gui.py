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
app.edit_recovery.show()
root.update()
viewer = app.edit_recovery.viewer
viewer.geometry("640x400")
root.update()
buttons = []
def inspect(widget):
    for child in widget.winfo_children():
        if child.winfo_class() == "TButton":
            buttons.append(child)
        inspect(child)
inspect(viewer)
assert any(button.cget("text") == "Clear all" for button in buttons)
for button in buttons:
    assert button.winfo_ismapped()
    assert button.winfo_rooty() + button.winfo_height() <= viewer.winfo_rooty() + viewer.winfo_height()
viewer.destroy()
app.on_close()
print('Linux GUI construction smoke test passed (no NWN or AI request).')
