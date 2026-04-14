#!/usr/bin/env python3
"""
Bobtrax Unified Launcher

This script serves as the interim unified entry point for the Bobtrax ecosystem.
Currently, `bobui` is a fork of QtBase and does not yet have the front-end DAW
launching UI completely implemented.

This script bridges that gap by providing a command-line interface to launch
any of the compiled submodules (Ardour, LMMS, MusE, Zrythm).

Design Decisions:
1. Subprocess management: Uses Python's `subprocess` module to spawn DAWs
   as independent child processes. This ensures that if the launcher crashes,
   it does not necessarily take down the DAW session.
2. Extensibility: The dictionary-based configuration (`DAW_CONFIG`) allows
   easy addition of new tools or modification of executable paths.
3. Fallback: Checks for executable existence before launching and provides
   helpful error messages guiding the user to run `./build.sh`.
"""

import argparse
import subprocess
import os
import sys

# Configuration mapping for each DAW
# Key: Command line argument
# Value: Dictionary containing 'name' and relative 'path' to the executable
DAW_CONFIG = {
    'ardour': {
        'name': 'Ardour',
        'path': 'ardour/gtk2_ardour/ardour'
    },
    'lmms': {
        'name': 'LMMS',
        'path': 'lmms/build/lmms'
    },
    'muse': {
        'name': 'MusE',
        'path': 'muse/src/build/muse/muse4'
    },
    'zrythm': {
        'name': 'Zrythm',
        'path': 'zrythm/build/src/zrythm'
    }
}

def launch_daw(daw_key):
    """
    Launches the specified DAW using subprocess.
    """
    config = DAW_CONFIG.get(daw_key)
    if not config:
        print(f"Error: Unknown DAW '{daw_key}'")
        sys.exit(1)

    exe_path = os.path.abspath(config['path'])
    name = config['name']

    print(f"[{name}] Attempting to launch...")
    print(f"[{name}] Executable path: {exe_path}")

    if not os.path.exists(exe_path):
        print(f"[{name}] Error: Executable not found at {exe_path}.")
        print(f"[{name}] Have you built it yet? Try running: ./build.sh --only-{daw_key}")
        sys.exit(1)

    if not os.access(exe_path, os.X_OK):
        print(f"[{name}] Error: File exists but is not executable.")
        sys.exit(1)

    try:
        # Launching as a detached process (or waiting if preferred, here we wait for console output)
        print(f"[{name}] Launching {name}...")
        subprocess.run([exe_path])
    except KeyboardInterrupt:
        print(f"\n[{name}] Execution interrupted by user.")
    except Exception as e:
        print(f"[{name}] An unexpected error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="Bobtrax Unified DAW Launcher")
    parser.add_argument(
        'daw',
        choices=list(DAW_CONFIG.keys()),
        help="The DAW to launch (ardour, lmms, muse, zrythm)"
    )

    args = parser.parse_args()
    launch_daw(args.daw)

if __name__ == '__main__':
    main()
