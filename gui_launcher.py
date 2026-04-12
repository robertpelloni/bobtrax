#!/usr/bin/env python3
"""
Bobtrax Unified GUI Launcher (Interim)

This script provides a lightweight, graphical entry point using tkinter.
It serves as a temporary visual interface until `bobui` (the QtBase fork)
is fully implemented with DAW-launching logic.

Features:
- Dynamically loads configuration from the existing `launcher.py` module.
- Displays a graphical window with buttons to launch each DAW.
- Spawns DAWs as detached subprocesses so the launcher can be closed
  without terminating the audio session.
- Graceful error handling via popup messages.
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import os

try:
    import launcher
except ImportError:
    messagebox.showerror("Error", "Could not find launcher.py configuration module.")
    exit(1)

def launch_daw_gui(daw_key):
    """
    Handles the click event for a DAW button.
    """
    config = launcher.DAW_CONFIG.get(daw_key)
    if not config:
        messagebox.showerror("Error", f"Unknown DAW '{daw_key}'")
        return

    exe_path = os.path.abspath(config['path'])
    name = config['name']

    if not os.path.exists(exe_path):
        messagebox.showerror(
            "Executable Not Found",
            f"Cannot find {name} executable at:\n{exe_path}\n\nHave you run ./build.sh?"
        )
        return

    if not os.access(exe_path, os.X_OK):
        messagebox.showerror("Permissions Error", f"{name} file exists but is not executable.")
        return

    try:
        # Spawn the process detached
        subprocess.Popen([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Optionally, show a brief transient notification or simply rely on the DAW window appearing
    except Exception as e:
        messagebox.showerror("Launch Error", f"Failed to launch {name}:\n{e}")

def main():
    root = tk.Tk()
    root.title("Bobtrax Omni-Launcher")
    root.geometry("400x300")
    root.eval('tk::PlaceWindow . center')

    # Simple styling
    root.configure(padx=20, pady=20)

    header = tk.Label(
        root,
        text="Bobtrax Audio Ecosystem",
        font=("Helvetica", 16, "bold")
    )
    header.pack(pady=(0, 20))

    subtitle = tk.Label(
        root,
        text="Select a Digital Audio Workstation to launch:",
        font=("Helvetica", 10)
    )
    subtitle.pack(pady=(0, 20))

    # Create a button for each configured DAW
    for key, config in launcher.DAW_CONFIG.items():
        btn = tk.Button(
            root,
            text=f"Launch {config['name']}",
            command=lambda k=key: launch_daw_gui(k),
            width=30,
            height=2,
            font=("Helvetica", 11)
        )
        btn.pack(pady=5)

    root.mainloop()

if __name__ == '__main__':
    main()
