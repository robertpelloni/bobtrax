#!/usr/bin/env python3
"""
Bobtrax Unified GUI Dashboard (Omni-Launcher)

This script provides a graphical entry point using tkinter.
It serves as the universal dashboard containing all high-value features
on a single unified page:
1. Native DAW Launching
2. AI Mixing Assistant
3. WebAssembly Host
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import subprocess
import os
import sys

try:
    import launcher
except ImportError:
    messagebox.showerror("Error", "Could not find launcher.py configuration module.")
    exit(1)

# Paths to backend scripts
AI_ASSISTANT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "ai_assistant"))
MIXING_ASSISTANT_PY = os.path.join(AI_ASSISTANT_DIR, "mixing_assistant.py")
WASM_HOST_PY = os.path.abspath(os.path.join(os.path.dirname(__file__), "bobui/src/bobtrax_launcher/wasm_host.py"))

class ToolTip(object):
    """
    Create a tooltip for a given widget.
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        try:
            bbox = self.widget.bbox("insert")
            if bbox:
                x, y, cx, cy = bbox
        except AttributeError:
            pass # bbox doesn't exist for many widgets like buttons

        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

class OmniDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bobtrax Omni-Dashboard")
        self.geometry("600x700")
        self.eval('tk::PlaceWindow . center')

        # State
        self.wasm_process = None
        self.selected_stems = []

        self.build_ui()

    def build_ui(self):
        # Header
        header = tk.Label(self, text="Bobtrax Universal Production Ecosystem", font=("Helvetica", 14, "bold"))
        header.pack(pady=(10, 5))
        ToolTip(header, "This is your single-page command center for all Bobtrax features.")

        # --- SECTION 0: MUSE Command Palette ---
        muse_frame = tk.LabelFrame(self, text="MUSE Command Palette", font=("Helvetica", 11, "bold"), padx=10, pady=10)
        muse_frame.pack(fill="x", padx=15, pady=5)
        ToolTip(muse_frame, "Unified Search Bar. Type a command like 'Add Compressor' to intelligently apply actions to the active DAW.")

        self.muse_prompt = tk.Entry(muse_frame, width=50)
        self.muse_prompt.insert(0, "Search or type command...")
        self.muse_prompt.pack(pady=5)
        ToolTip(self.muse_prompt, "Press Enter to execute the command across the ecosystem.")
        self.muse_prompt.bind("<Return>", self.execute_muse_command)

        # --- SECTION 1: AI Mixing Assistant (Highest Value) ---
        ai_frame = tk.LabelFrame(self, text="AI Mixing Assistant", font=("Helvetica", 11, "bold"), padx=10, pady=10)
        ai_frame.pack(fill="x", padx=15, pady=5)
        ToolTip(ai_frame, "Use natural language to autonomously control and mix tracks across all your open DAWs via OSC.")

        self.ai_prompt = tk.Entry(ai_frame, width=50)
        self.ai_prompt.insert(0, "e.g., 'Make the kick punchy and reduce the bass'")
        self.ai_prompt.pack(pady=5)
        ToolTip(self.ai_prompt, "Type a natural language instruction here. The AI will translate it into specific OSC mixing parameters.")

        stem_btn_frame = tk.Frame(ai_frame)
        stem_btn_frame.pack(fill="x", pady=5)

        self.load_stems_btn = tk.Button(stem_btn_frame, text="Load Stems (Context)", command=self.load_stems)
        self.load_stems_btn.pack(side="left")
        ToolTip(self.load_stems_btn, "Select multitrack stems (like those output from Demucs) to provide the AI with context about the session.")

        self.stem_lbl = tk.Label(stem_btn_frame, text="No stems loaded.", fg="gray")
        self.stem_lbl.pack(side="left", padx=10)

        self.exec_mix_btn = tk.Button(ai_frame, text="Execute AI Mix", bg="#4CAF50", fg="white", command=self.execute_mix)
        self.exec_mix_btn.pack(pady=5)
        ToolTip(self.exec_mix_btn, "Sends your prompt to the local LLM which will parse it into JSON arrays of OSC moves and apply them to the DAWs.")

        # --- SECTION 2: WebAssembly Collaboration Host ---
        wasm_frame = tk.LabelFrame(self, text="WebAssembly Collaboration Host", font=("Helvetica", 11, "bold"), padx=10, pady=10)
        wasm_frame.pack(fill="x", padx=15, pady=5)
        ToolTip(wasm_frame, "Spin up a local server to run the C++ audio engines directly in your browser for decentralized collaboration.")

        wasm_btn_frame = tk.Frame(wasm_frame)
        wasm_btn_frame.pack()

        self.start_wasm_btn = tk.Button(wasm_btn_frame, text="Start Server", command=self.start_wasm)
        self.start_wasm_btn.pack(side="left", padx=5)
        ToolTip(self.start_wasm_btn, "Initializes the local python http.server which serves the WebAssembly audio engine files to your browser.")

        self.stop_wasm_btn = tk.Button(wasm_btn_frame, text="Stop Server", command=self.stop_wasm, state="disabled")
        self.stop_wasm_btn.pack(side="left", padx=5)
        ToolTip(self.stop_wasm_btn, "Terminates the local WebAssembly collaboration server.")

        # --- SECTION 3: Native DAWs ---
        daw_frame = tk.LabelFrame(self, text="Native Audio Workstations", font=("Helvetica", 11, "bold"), padx=10, pady=10)
        daw_frame.pack(fill="x", padx=15, pady=5)
        ToolTip(daw_frame, "Launch the fully compiled, native C/C++ Digital Audio Workstations.")

        for key, config in launcher.DAW_CONFIG.items():
            btn = tk.Button(
                daw_frame,
                text=f"Launch {config['name']}",
                command=lambda k=key: self.launch_daw_gui(k),
                width=20
            )
            btn.pack(side="left", padx=5, expand=True)
            ToolTip(btn, f"Launch the {config['name']} native binary as a detached subprocess.")

        # --- SECTION 4: Unified Log ---
        log_frame = tk.LabelFrame(self, text="System Log", font=("Helvetica", 11, "bold"), padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.log_text = tk.Text(log_frame, height=10, bg="#f4f4f4", state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def load_stems(self):
        stems = filedialog.askopenfilenames(title="Select Stem Files")
        if stems:
            self.selected_stems = stems
            self.stem_lbl.config(text=f"Loaded {len(stems)} stems.")
            self.log(f"Loaded stems: {', '.join([os.path.basename(s) for s in stems])}")

    def execute_muse_command(self, event=None):
        cmd = self.muse_prompt.get()
        if cmd and cmd != "Search or type command...":
            self.log(f"[MUSE Command Palette] Executing: {cmd}")
            # Placeholder for actual cross-DAW routing logic
            self.log(f"Routing '{cmd}' to active DAW (stub).")
            self.muse_prompt.delete(0, tk.END)

    def execute_mix(self):
        prompt = self.ai_prompt.get()
        if not prompt or prompt == "e.g., 'Make the kick punchy and reduce the bass'":
            self.log("Error: Please enter a valid prompt.")
            return

        self.log(f"Executing AI Mix: '{prompt}'")
        stem_names = [os.path.splitext(os.path.basename(s))[0] for s in self.selected_stems]
        env = os.environ.copy()
        if stem_names:
            env["BOBTRAX_TRACKS"] = ",".join(stem_names)

        try:
            cmd = [sys.executable, MIXING_ASSISTANT_PY, prompt]
            if not os.environ.get("OPENAI_API_KEY"):
                cmd.extend(["--llm-url", "http://localhost:1234/v1"]) # Mock URL

            self.log("Waiting for LLM response...")
            import threading
            def run_assistant():
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                    # Safely schedule log updates in main thread
                    if result.stdout:
                        self.after(0, lambda: self.log(result.stdout.strip()))
                    if result.stderr:
                        self.after(0, lambda: self.log(result.stderr.strip()))
                except Exception as e:
                    err_msg = f"Exception during AI execution: {e}"
                    self.after(0, lambda: self.log(err_msg))

            threading.Thread(target=run_assistant, daemon=True).start()

        except Exception as e:
            self.log(f"Exception during AI execution: {e}")

    def start_wasm(self):
        if not self.wasm_process:
            self.log("Starting WebAssembly local server...")
            try:
                self.wasm_process = subprocess.Popen(
                    [sys.executable, WASM_HOST_PY],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                self.log("WASM Server started. Navigate browser to http://localhost:8080")
                self.start_wasm_btn.config(state="disabled")
                self.stop_wasm_btn.config(state="normal")
            except Exception as e:
                self.log(f"Failed to start server: {e}")

    def stop_wasm(self):
        if self.wasm_process:
            self.log("Stopping WebAssembly server...")
            self.wasm_process.terminate()
            self.wasm_process.wait()
            self.wasm_process = None
            self.log("Server stopped.")
            self.start_wasm_btn.config(state="normal")
            self.stop_wasm_btn.config(state="disabled")

    def launch_daw_gui(self, daw_key):
        config = launcher.DAW_CONFIG.get(daw_key)
        exe_path = os.path.abspath(config['path'])
        name = config['name']

        if not os.path.exists(exe_path):
            messagebox.showerror("Executable Not Found", f"Cannot find {name} at:\n{exe_path}\n\nRun ./build.sh")
            return

        try:
            self.log(f"Launching native DAW: {name}")
            subprocess.Popen([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.log(f"Failed to launch {name}: {e}")

if __name__ == '__main__':
    app = OmniDashboard()
    app.mainloop()
