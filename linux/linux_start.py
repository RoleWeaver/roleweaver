"""Preflight the Linux desktop before importing GUI/input dependencies."""
import sys
from linux_platform import require_desktop


def main():
    try:
        require_desktop()
        import tkinter as tk
        # Probe display access before pynput initializes its X11 connection.
        probe = tk.Tk()
        probe.withdraw()
        probe.destroy()
        import nwn_ai_gui
        nwn_ai_gui.main()
    except Exception as exc:
        print(f'Role Weaver could not start: {exc}', file=sys.stderr)
        print('See INSTALL_LINUX.md. Run bash start-role-weaver.sh from a desktop terminal for diagnostics.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
