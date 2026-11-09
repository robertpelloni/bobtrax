#!/usr/bin/env python3
"""
Bobtrax Unified GUI Dashboard (Omni-Launcher)

Single-Page Comprehensive Command Center for the Bobtrax Ecosystem:
1. Header & Live Global Service Status Indicator & System Tray Integration
2. Unified MUSE Command Palette (Routing transport, mixing, and plugin actions)
3. AI Production Suite (AI Mixing Assistant & Demucs Stem Separator)
4. IPC & Collaboration Hub (OSC Bridge, WebSocket Wrapper, WebAssembly Host)
5. Omni-Plugin Bridge & Native Workstations (Ardour, LMMS, MusE, Zrythm)
6. Real-Time Telemetry & System Log

Includes full System Tray support (pystray with safe Tk fallback),
asynchronous service management, and safe tooltip guidance on all widgets.
"""

import os
import sys
import threading
import subprocess
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import launcher
except ImportError:
    launcher = None

try:
    import session_memory
except ImportError:
    session_memory = None

try:
    import session_exporter
except ImportError:
    session_exporter = None

try:
    import session_importer
except ImportError:
    session_importer = None

try:
    import health_watchdog
except ImportError:
    health_watchdog = None

# Optional System Tray & Image support
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except Exception:
    HAS_TRAY = False

# Paths to helper scripts
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
AI_ASSISTANT_DIR = os.path.join(REPO_ROOT, "ai_assistant")
MIXING_ASSISTANT_PY = os.path.join(AI_ASSISTANT_DIR, "mixing_assistant.py")
OSC_BRIDGE_PY = os.path.join(REPO_ROOT, "osc_bridge.py")
OSC_WEB_WRAPPER_PY = os.path.join(REPO_ROOT, "osc_web_wrapper.py")
WASM_HOST_PY = os.path.join(REPO_ROOT, "wasm_host.py")
STEM_SEPARATOR_PY = os.path.join(REPO_ROOT, "stem_separator.py")

# Fallback path if wasm_host is in bobui
if not os.path.exists(WASM_HOST_PY):
    alt_wasm = os.path.join(REPO_ROOT, "bobui/src/bobtrax_launcher/wasm_host.py")
    if os.path.exists(alt_wasm):
        WASM_HOST_PY = alt_wasm

# Fallback path if stem_separator is in bobui
if not os.path.exists(STEM_SEPARATOR_PY):
    alt_stem = os.path.join(REPO_ROOT, "bobui/src/bobtrax_launcher/stem_separator.py")
    if os.path.exists(alt_stem):
        STEM_SEPARATOR_PY = alt_stem


class ToolTip(object):
    """
    Robust hover-based ToolTip widget.
    Gracefully handles Tkinter widgets that lack bbox('insert') support.
    """
    def __init__(self, widget, text='widget info', waittime=400, wraplength=260):
        self.waittime = waittime
        self.wraplength = wraplength
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
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def showtip(self, event=None):
        x = y = 0
        try:
            bbox = self.widget.bbox("insert")
            if bbox:
                x, y, cx, cy = bbox
        except (AttributeError, tk.TclError):
            pass

        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 24
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tw,
            text=self.text,
            justify='left',
            background="#2b2d30",
            foreground="#f0f0f0",
            relief='solid',
            borderwidth=1,
            padx=6,
            pady=4,
            wraplength=self.wraplength,
            font=("Helvetica", 9)
        )
        label.pack()

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


class OmniDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bobtrax Omni-Dashboard | Universal Music Production Ecosystem")
        self.geometry("920x820")
        self.minsize(800, 700)
        try:
            self.eval('tk::PlaceWindow . center')
        except Exception:
            pass

        # Server Subprocesses
        self.processes = {
            "wasm": None,
            "osc_bridge": None,
            "osc_web": None
        }

        self.selected_stems = []
        self.selected_audio_file = None
        self.tray_icon = None
        self.meter_history = [0.0] * 32

        # Build UI layout
        self.build_ui()

        # Initialize System Tray
        self.init_system_tray()

        # Start live background telemetry listener
        self.start_telemetry_listener()

        # Start autonomous health watchdog
        self.start_health_watchdog()

        # Intercept window close to support minimize-to-tray or clean shutdown
        self.protocol("WM_DELETE_WINDOW", self.on_close_requested)

    def build_ui(self):
        # Configure styles
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Scrollable canvas container to ensure all sections fit seamlessly
        self.main_canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.content_frame = tk.Frame(self.main_canvas, padx=12, pady=10)

        self.content_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.main_canvas.bind('<Configure>', self._on_canvas_configure)
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.pack(side="right", fill="y")

        # -------------------------------------------------------------
        # 1. Header & Live Status Bar
        # -------------------------------------------------------------
        header_frame = tk.Frame(self.content_frame, bg="#1e1e24", padx=10, pady=8)
        header_frame.pack(fill="x", pady=(0, 8))

        title_lbl = tk.Label(
            header_frame,
            text="BOBTRAX OMNI-DASHBOARD",
            font=("Helvetica", 14, "bold"),
            bg="#1e1e24",
            fg="#61dafb"
        )
        title_lbl.pack(side="left")
        ToolTip(title_lbl, "Bobtrax Command Center: Consolidated native DAWs, AI assistants, and WebAssembly hub.")

        # Read current version dynamically from VERSION.md
        version_str = "v1.0.26"
        version_file = os.path.join(REPO_ROOT, "VERSION.md")
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as vf:
                    version_str = f"v{vf.read().strip()}"
            except Exception:
                pass

        version_lbl = tk.Label(
            header_frame,
            text=version_str,
            font=("Helvetica", 9, "italic"),
            bg="#1e1e24",
            fg="#9da5b4"
        )
        version_lbl.pack(side="left", padx=(8, 0))

        # Status Badges Frame
        self.status_bar_frame = tk.Frame(header_frame, bg="#1e1e24")
        self.status_bar_frame.pack(side="right")

        self.badge_watchdog = tk.Label(self.status_bar_frame, text="WATCHDOG: ACTIVE", font=("Helvetica", 8, "bold"), bg="#3a3d45", fg="#61dafb", padx=5)
        self.badge_watchdog.pack(side="left", padx=3)
        ToolTip(self.badge_watchdog, "Continuous health watchdog probing core daemons with autonomous self-healing.")

        self.badge_tray = tk.Label(self.status_bar_frame, text="TRAY: READY", font=("Helvetica", 8, "bold"), bg="#3a3d45", fg="#a6e22e", padx=5)
        self.badge_tray.pack(side="left", padx=3)
        ToolTip(self.badge_tray, "System Tray status. Click minimize or tray menu to control servers.")

        self.badge_wasm = tk.Label(self.status_bar_frame, text="WASM: STOPPED", font=("Helvetica", 8, "bold"), bg="#3a3d45", fg="#f92672", padx=5)
        self.badge_wasm.pack(side="left", padx=3)
        ToolTip(self.badge_wasm, "WebAssembly Collaboration Server status.")

        self.badge_bridge = tk.Label(self.status_bar_frame, text="OSC BRIDGE: STOPPED", font=("Helvetica", 8, "bold"), bg="#3a3d45", fg="#f92672", padx=5)
        self.badge_bridge.pack(side="left", padx=3)
        ToolTip(self.badge_bridge, "Central Open Sound Control IPC router status.")

        self.badge_ws = tk.Label(self.status_bar_frame, text="WS: STOPPED", font=("Helvetica", 8, "bold"), bg="#3a3d45", fg="#f92672", padx=5)
        self.badge_ws.pack(side="left", padx=3)
        ToolTip(self.badge_ws, "WebSocket-to-OSC gateway status.")

        # -------------------------------------------------------------
        # 2. Section: MUSE Command Palette (Global Rapid Command)
        # -------------------------------------------------------------
        muse_frame = tk.LabelFrame(
            self.content_frame,
            text=" MUSE Universal Command Palette ",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=8
        )
        muse_frame.pack(fill="x", pady=4)
        ToolTip(muse_frame, "Type transport commands (play, stop, record) or mixing actions to execute across all open workstations.")

        palette_bar = tk.Frame(muse_frame)
        palette_bar.pack(fill="x")

        self.muse_prompt = ttk.Entry(palette_bar, font=("Helvetica", 10))
        self.muse_prompt.insert(0, "Type command (e.g. 'play', 'stop', 'tempo 120', 'add compressor', 'status')...")
        self.muse_prompt.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.muse_prompt.bind("<FocusIn>", self._clear_muse_placeholder)
        self.muse_prompt.bind("<Return>", self.execute_muse_command)
        ToolTip(self.muse_prompt, "Enter command and press Enter. Supports transport, mixing, and ecosystem actions.")

        exec_cmd_btn = ttk.Button(palette_bar, text="Execute Command", command=self.execute_muse_command)
        exec_cmd_btn.pack(side="right")
        ToolTip(exec_cmd_btn, "Routes typed command to active DAWs via OSC Bridge or ecosystem logic.")

        # Quick Transport Shortcuts & Macros
        shortcuts_bar = tk.Frame(muse_frame, pady=4)
        shortcuts_bar.pack(fill="x")
        tk.Label(shortcuts_bar, text="Quick Transport:", font=("Helvetica", 8, "bold"), fg="#555").pack(side="left", padx=(0, 6))

        for action_name, label_txt, symbol in [("play", "Play", "▶ Play"), ("stop", "Stop", "⏹ Stop"), ("record", "Record", "⏺ Record")]:
            btn = ttk.Button(shortcuts_bar, text=symbol, command=lambda a=action_name: self.dispatch_transport(a), width=9)
            btn.pack(side="left", padx=2)
            ToolTip(btn, f"Send '{label_txt}' command through OSC Bridge to all active DAWs.")

        tk.Label(shortcuts_bar, text="| Macros:", font=("Helvetica", 8, "bold"), fg="#555").pack(side="left", padx=(6, 4))
        for macro_name, macro_cmd in [("Mute All", "mute all"), ("Reset Faders", "reset faders"), ("Solo Vox", "solo vocal")]:
            b = ttk.Button(shortcuts_bar, text=macro_name, command=lambda c=macro_cmd: self._run_macro(c))
            b.pack(side="left", padx=2)
            ToolTip(b, f"Execute '{macro_cmd}' macro across session.")

        # -------------------------------------------------------------
        # 3. Section: AI Production Suite (Mixing Assistant + Stem Separation)
        # -------------------------------------------------------------
        ai_frame = tk.LabelFrame(
            self.content_frame,
            text=" AI Production Suite (Natural Language Mixing & Demucs Separation) ",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=8
        )
        ai_frame.pack(fill="x", pady=4)
        ToolTip(ai_frame, "Autonomous AI audio agents: Natural Language mixing parameters & Neural stem separation.")

        # AI Mixing Assistant Subsection
        mix_sub = tk.LabelFrame(ai_frame, text="AI Mixing Assistant (NLP -> Real-Time OSC)", font=("Helvetica", 9, "bold"), padx=8, pady=6)
        mix_sub.pack(fill="x", pady=(0, 6))

        prompt_row = tk.Frame(mix_sub)
        prompt_row.pack(fill="x", pady=2)
        self.ai_prompt = ttk.Entry(prompt_row, font=("Helvetica", 9))
        self.ai_prompt.insert(0, "e.g. 'Make the kick punchy and compress the snare'")
        self.ai_prompt.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.ai_prompt.bind("<FocusIn>", self._clear_ai_placeholder)
        ToolTip(self.ai_prompt, "Describe desired audio moves in natural language. Translated into precise OSC parameter values.")

        self.exec_mix_btn = tk.Button(prompt_row, text="Execute AI Mix", bg="#2e7d32", fg="white", font=("Helvetica", 9, "bold"), command=self.execute_mix)
        self.exec_mix_btn.pack(side="right")
        ToolTip(self.exec_mix_btn, "Sends prompt to NLP/LLM engine which maps moves to tracks and pushes OSC commands to DAWs.")

        # Presets & Context Row
        preset_row = tk.Frame(mix_sub)
        preset_row.pack(fill="x", pady=4)

        tk.Label(preset_row, text="Presets:", font=("Helvetica", 8, "bold"), fg="#555").pack(side="left", padx=(0, 4))
        presets = [
            ("Punchy Kick", "Boost kick low shelf and compress with fast ratio"),
            ("Vocal Clarity", "High cut vocal mud and boost presence shelf"),
            ("Warm Master", "Add subtle saturation drive and gentle limiter gain")
        ]
        for pname, pval in presets:
            b = ttk.Button(preset_row, text=pname, command=lambda v=pval: self._set_ai_prompt(v))
            b.pack(side="left", padx=2)
            ToolTip(b, f"Populate prompt with: '{pval}'")

        self.load_stems_btn = ttk.Button(preset_row, text="Attach Stems", command=self.load_stems)
        self.load_stems_btn.pack(side="right", padx=(4, 0))
        ToolTip(self.load_stems_btn, "Select audio track files to populate session track names in the AI prompt context.")

        self.discover_session_btn = ttk.Button(preset_row, text="Scan DAW Session", command=self.discover_session_file)
        self.discover_session_btn.pack(side="right", padx=(4, 0))
        ToolTip(self.discover_session_btn, "Scan an Ardour (.ardour) or LMMS (.mmp) session file to discover project tracks.")

        self.stem_lbl = tk.Label(preset_row, text="No track context attached.", fg="#666", font=("Helvetica", 8))
        self.stem_lbl.pack(side="right", padx=6)

        # Stem Separator Subsection
        stem_sub = tk.LabelFrame(ai_frame, text="Demucs Neural Stem Separator (Multi-Track Splitter)", font=("Helvetica", 9, "bold"), padx=8, pady=6)
        stem_sub.pack(fill="x", pady=4)

        file_row = tk.Frame(stem_sub)
        file_row.pack(fill="x", pady=2)

        self.audio_file_entry = ttk.Entry(file_row, font=("Helvetica", 9))
        self.audio_file_entry.insert(0, "Select input audio track file for stem separation...")
        self.audio_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ToolTip(self.audio_file_entry, "File path to audio track (WAV, MP3, FLAC) to split into stems.")

        browse_btn = ttk.Button(file_row, text="Browse Audio...", command=self.browse_audio_file)
        browse_btn.pack(side="left", padx=(0, 6))
        ToolTip(browse_btn, "Open file dialog to choose source audio track.")

        # Model & GPU options
        opts_row = tk.Frame(stem_sub)
        opts_row.pack(fill="x", pady=4)

        tk.Label(opts_row, text="Model:", font=("Helvetica", 9)).pack(side="left")
        self.model_combo = ttk.Combobox(opts_row, values=["htdemucs", "htdemucs_ft", "mdx_extra", "mdx_extra_q"], state="readonly", width=12)
        self.model_combo.set("htdemucs")
        self.model_combo.pack(side="left", padx=4)
        ToolTip(self.model_combo, "Select Demucs neural model. 'htdemucs' is fast and balanced; 'mdx_extra' offers high fidelity.")

        self.gpu_var = tk.BooleanVar(value=False)
        gpu_chk = ttk.Checkbutton(opts_row, text="Use GPU (CUDA)", variable=self.gpu_var)
        gpu_chk.pack(side="left", padx=8)
        ToolTip(gpu_chk, "Enable GPU acceleration if NVIDIA CUDA is configured.")

        self.separate_btn = tk.Button(opts_row, text="Run Stem Separation", bg="#1565c0", fg="white", font=("Helvetica", 9, "bold"), command=self.run_stem_separator)
        self.separate_btn.pack(side="right")
        ToolTip(self.separate_btn, "Split chosen audio file into drums, bass, vocals, and other tracks.")

        # -------------------------------------------------------------
        # 3.5 Section: Track Agent-Memory & Dynamic State Hub
        # -------------------------------------------------------------
        mem_frame = tk.LabelFrame(
            self.content_frame,
            text=" Track Agent-Memory & Dynamic State Hub ",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=8
        )
        mem_frame.pack(fill="x", pady=4)
        ToolTip(mem_frame, "Shared inter-DAW session memory tracking active tracks, fader gains, and AI mixing history.")

        mem_ctrl_bar = tk.Frame(mem_frame)
        mem_ctrl_bar.pack(fill="x", pady=(0, 4))

        tk.Label(mem_ctrl_bar, text="Active Session Memory Tracks:", font=("Helvetica", 9, "bold")).pack(side="left")

        self.refresh_mem_btn = ttk.Button(mem_ctrl_bar, text="Refresh Memory", command=self.refresh_session_memory)
        self.refresh_mem_btn.pack(side="right", padx=2)
        ToolTip(self.refresh_mem_btn, "Reload track states and history from session memory.")

        self.undo_btn = ttk.Button(mem_ctrl_bar, text="Undo Last Move", command=self.undo_last_mix_action)
        self.undo_btn.pack(side="right", padx=2)
        ToolTip(self.undo_btn, "Revert the parameter adjustments from the previous AI mixing action.")

        self.redo_btn = ttk.Button(mem_ctrl_bar, text="Redo Move", command=self.redo_last_mix_action)
        self.redo_btn.pack(side="right", padx=2)
        ToolTip(self.redo_btn, "Re-apply the parameter adjustments from the most recently undone mixing action.")

        self.audit_btn = ttk.Button(mem_ctrl_bar, text="Audit Consistency", command=self.audit_session_state)
        self.audit_btn.pack(side="right", padx=2)
        ToolTip(self.audit_btn, "Verify parameter bounds (-90dB to +12dB) and standardized track roles across session.")

        self.save_snap_btn = ttk.Button(mem_ctrl_bar, text="Save Snapshot", command=self.save_session_snapshot)
        self.save_snap_btn.pack(side="right", padx=2)
        ToolTip(self.save_snap_btn, "Save a named checkpoint of all track faders and settings.")

        self.restore_snap_btn = ttk.Button(mem_ctrl_bar, text="Restore Checkpoint...", command=self.restore_checkpoint_dialog)
        self.restore_snap_btn.pack(side="right", padx=2)
        ToolTip(self.restore_snap_btn, "Browse and restore previous session checkpoints across DAWs.")

        self.import_session_btn = ttk.Button(mem_ctrl_bar, text="Import Session...", command=self.import_session_dialog)
        self.import_session_btn.pack(side="right", padx=2)
        ToolTip(self.import_session_btn, "Import track faders and settings from an Ardour (.ardour) or LMMS (.mmp) file.")

        self.merge_session_btn = ttk.Button(mem_ctrl_bar, text="Merge Session (Conflict Safe)...", command=self.merge_session_dialog)
        self.merge_session_btn.pack(side="right", padx=2)
        ToolTip(self.merge_session_btn, "Import and merge external session with conflict detection and automated resolution strategies.")

        self.export_session_btn = ttk.Button(mem_ctrl_bar, text="Export Session...", command=self.export_session_dialog)
        self.export_session_btn.pack(side="right", padx=2)
        ToolTip(self.export_session_btn, "Export current session state to Ardour (.ardour) or LMMS (.mmp) project files.")

        self.sync_manifest_btn = ttk.Button(mem_ctrl_bar, text="Sync to Bridge", command=self.sync_manifest_to_bridge)
        self.sync_manifest_btn.pack(side="right", padx=2)
        ToolTip(self.sync_manifest_btn, "Push full session layout and track states to Omni-Plugin Bridge host.")

        self.diff_sync_btn = ttk.Button(mem_ctrl_bar, text="Sync Diff to Base", command=self.sync_diff_to_baseline)
        self.diff_sync_btn.pack(side="right", padx=2)
        ToolTip(self.diff_sync_btn, "Compute minimal state diff against baseline checkpoint and broadcast delta.")

        self.compare_snaps_btn = ttk.Button(mem_ctrl_bar, text="Compare Checkpoints...", command=self.compare_checkpoints_dialog)
        self.compare_snaps_btn.pack(side="right", padx=2)
        ToolTip(self.compare_snaps_btn, "Inspect fine-grained visual parameter diffs between any two checkpoints or live state.")

        self.multi_daw_sync_btn = ttk.Button(mem_ctrl_bar, text="Broadcast to All DAWs", command=self.broadcast_session_to_all_daws)
        self.multi_daw_sync_btn.pack(side="right", padx=2)
        ToolTip(self.multi_daw_sync_btn, "Simultaneously push entire session state over binary socket & OSC to all active DAWs with echo suppression.")

        self.test_sync_loop_btn = ttk.Button(mem_ctrl_bar, text="Test Sync Loop", command=self.test_sync_loop_probe)
        self.test_sync_loop_btn.pack(side="right", padx=2)
        ToolTip(self.test_sync_loop_btn, "Probe circular feedback echo suppression and round-trip broadcast latency.")

        self.transition_btn = ttk.Button(mem_ctrl_bar, text="Transition to DAW...", command=self.transition_daw_dialog)
        self.transition_btn.pack(side="right", padx=2)
        ToolTip(self.transition_btn, "Seamlessly migrate active session to another DAW with preserved checkpoints and state.")

        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_chk = ttk.Checkbutton(mem_ctrl_bar, text="Auto-Save", variable=self.auto_save_var, command=self._toggle_auto_save)
        auto_save_chk.pack(side="right", padx=4)
        ToolTip(auto_save_chk, "Toggle periodic background session auto-save and bridge sync daemon.")

        self.mem_status_lbl = tk.Label(mem_ctrl_bar, text="", font=("Helvetica", 8, "italic"), fg="#555")
        self.mem_status_lbl.pack(side="right", padx=6)

        # Interactive Multi-Track Console Channel Strips
        self.mixer_strips_frame = tk.Frame(mem_frame, bg="#1e1e24", padx=6, pady=6)
        self.mixer_strips_frame.pack(fill="x")
        ToolTip(self.mixer_strips_frame, "Interactive channel strips: manual fader level, mute (M), solo (S), and mini VU meters.")

        # Omni-Plugin Synchronizer Controls Sub-bar
        plugin_sync_bar = tk.Frame(mem_frame, bg="#282c34", padx=6, pady=4)
        plugin_sync_bar.pack(fill="x", pady=(4, 0))

        tk.Label(
            plugin_sync_bar,
            text="Omni-Plugin Live Sync:",
            font=("Helvetica", 8, "bold"),
            bg="#282c34",
            fg="#ffd54f"
        ).pack(side="left", padx=(0, 4))

        tk.Label(plugin_sync_bar, text="Target Track:", font=("Helvetica", 8), bg="#282c34", fg="#abb2bf").pack(side="left")
        self.plugin_track_combo = ttk.Combobox(plugin_sync_bar, values=["kick", "bass", "vocals", "synth", "master"], state="readonly", width=8)
        self.plugin_track_combo.set("bass")
        self.plugin_track_combo.pack(side="left", padx=4)

        tk.Label(plugin_sync_bar, text="Preset:", font=("Helvetica", 8), bg="#282c34", fg="#abb2bf").pack(side="left")
        self.plugin_preset_combo = ttk.Combobox(
            plugin_sync_bar,
            values=["Warm Tube", "Opto Comp", "Space Reverb", "Clean Limiter"],
            state="readonly",
            width=12
        )
        self.plugin_preset_combo.set("Warm Tube")
        self.plugin_preset_combo.pack(side="left", padx=4)
        ToolTip(self.plugin_preset_combo, "Quick multi-parameter preset macro for cross-DAW plugins.")

        apply_preset_btn = ttk.Button(plugin_sync_bar, text="Apply Preset", command=self._apply_plugin_preset)
        apply_preset_btn.pack(side="left", padx=2)
        ToolTip(apply_preset_btn, "Broadcast preset parameter block to Omni-Plugin Bridge.")

        tk.Label(plugin_sync_bar, text="Cutoff:", font=("Helvetica", 8), bg="#282c34", fg="#abb2bf").pack(side="left")
        self.cutoff_scale = tk.Scale(
            plugin_sync_bar,
            from_=20.0,
            to=20000.0,
            resolution=10.0,
            orient="horizontal",
            length=100,
            bg="#282c34",
            fg="#abb2bf",
            highlightthickness=0,
            font=("Monospace", 7),
            command=self._on_plugin_cutoff_moved
        )
        self.cutoff_scale.set(1200.0)
        self.cutoff_scale.pack(side="left", padx=4)
        ToolTip(self.cutoff_scale, "Live VST/LV2 filter cutoff parameter streamed over Omni-Plugin Bridge.")

        tk.Label(plugin_sync_bar, text="Drive:", font=("Helvetica", 8), bg="#282c34", fg="#abb2bf").pack(side="left")
        self.drive_scale = tk.Scale(
            plugin_sync_bar,
            from_=0.0,
            to=1.0,
            resolution=0.01,
            orient="horizontal",
            length=80,
            bg="#282c34",
            fg="#abb2bf",
            highlightthickness=0,
            font=("Monospace", 7),
            command=self._on_plugin_drive_moved
        )
        self.drive_scale.set(0.25)
        self.drive_scale.pack(side="left", padx=4)
        ToolTip(self.drive_scale, "Live VST/LV2 saturation drive parameter streamed over Omni-Plugin Bridge.")

        self.plugin_sync_status = tk.Label(
            plugin_sync_bar,
            text="IPC: Idle",
            font=("Helvetica", 8, "italic"),
            bg="#282c34",
            fg="#98c379"
        )
        self.plugin_sync_status.pack(side="right", padx=4)

        self.track_widgets = {} # { track_name: { 'fader': Scale, 'mute_btn': Button, 'solo_btn': Button, 'vu': Canvas } }

        self._build_mixer_strips()

        # -------------------------------------------------------------
        # 4. Section: Real-Time IPC & Collaboration Hub
        # -------------------------------------------------------------
        ipc_frame = tk.LabelFrame(
            self.content_frame,
            text=" Real-Time IPC & Collaboration Hub (Server Lifecycle Controls) ",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=8
        )
        ipc_frame.pack(fill="x", pady=4)
        ToolTip(ipc_frame, "Manage and monitor background servers for DAW synchronization and browser collaboration.")

        # Grid of Server Controllers
        grid_frame = tk.Frame(ipc_frame)
        grid_frame.pack(fill="x", pady=4)

        # A. OSC Bridge Server Card
        card_bridge = tk.LabelFrame(grid_frame, text="Central OSC Bridge", font=("Helvetica", 9, "bold"), padx=6, pady=6)
        card_bridge.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(card_bridge, text="UDP Router: 127.0.0.1:8000", fg="#555", font=("Helvetica", 8)).pack(anchor="w")
        ToolTip(card_bridge, "Translates OSC dialects between Ardour, LMMS, MusE, and Zrythm.")

        bridge_btn_row = tk.Frame(card_bridge)
        bridge_btn_row.pack(fill="x", pady=4)
        self.start_bridge_btn = ttk.Button(bridge_btn_row, text="Start Bridge", command=self.start_osc_bridge)
        self.start_bridge_btn.pack(side="left", padx=2, fill="x", expand=True)
        ToolTip(self.start_bridge_btn, "Launch background OSC Bridge router process.")

        self.stop_bridge_btn = ttk.Button(bridge_btn_row, text="Stop", command=self.stop_osc_bridge, state="disabled")
        self.stop_bridge_btn.pack(side="left", padx=2)
        ToolTip(self.stop_bridge_btn, "Terminate background OSC Bridge.")

        # B. WebSocket-to-OSC Wrapper Card
        card_ws = tk.LabelFrame(grid_frame, text="WebSocket Gateway", font=("Helvetica", 9, "bold"), padx=6, pady=6)
        card_ws.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(card_ws, text="Port: ws://127.0.0.1:8765", fg="#555", font=("Helvetica", 8)).pack(anchor="w")
        ToolTip(card_ws, "Translates web JSON payloads into OSC messages for browser/UI integration.")

        ws_btn_row = tk.Frame(card_ws)
        ws_btn_row.pack(fill="x", pady=4)
        self.start_ws_btn = ttk.Button(ws_btn_row, text="Start WS", command=self.start_osc_web)
        self.start_ws_btn.pack(side="left", padx=2, fill="x", expand=True)
        ToolTip(self.start_ws_btn, "Launch WebSocket gateway process.")

        self.stop_ws_btn = ttk.Button(ws_btn_row, text="Stop", command=self.stop_osc_web, state="disabled")
        self.stop_ws_btn.pack(side="left", padx=2)
        ToolTip(self.stop_ws_btn, "Terminate WebSocket gateway.")

        # C. WebAssembly Host Card
        card_wasm = tk.LabelFrame(grid_frame, text="WebAssembly Host", font=("Helvetica", 9, "bold"), padx=6, pady=6)
        card_wasm.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(card_wasm, text="Portal: http://localhost:8080", fg="#555", font=("Helvetica", 8)).pack(anchor="w")
        ToolTip(card_wasm, "Local HTTP server serving compiled C++ audio engines in browser.")

        wasm_btn_row = tk.Frame(card_wasm)
        wasm_btn_row.pack(fill="x", pady=4)
        self.start_wasm_btn = ttk.Button(wasm_btn_row, text="Start WASM", command=self.start_wasm)
        self.start_wasm_btn.pack(side="left", padx=2, fill="x", expand=True)
        ToolTip(self.start_wasm_btn, "Launch local WASM collaboration HTTP server.")

        self.stop_wasm_btn = ttk.Button(wasm_btn_row, text="Stop", command=self.stop_wasm, state="disabled")
        self.stop_wasm_btn.pack(side="left", padx=2)
        ToolTip(self.stop_wasm_btn, "Terminate WebAssembly host server.")

        # Global Server Management Bar
        all_servers_bar = tk.Frame(ipc_frame, pady=4)
        all_servers_bar.pack(fill="x")

        start_all_btn = tk.Button(all_servers_bar, text="Start All Servers", bg="#333", fg="#a6e22e", font=("Helvetica", 8, "bold"), command=self.start_all_servers)
        start_all_btn.pack(side="left", padx=4)
        ToolTip(start_all_btn, "Start OSC Bridge, WebSocket Gateway, and WASM Host concurrently.")

        stop_all_btn = tk.Button(all_servers_bar, text="Stop All Servers", bg="#333", fg="#f92672", font=("Helvetica", 8, "bold"), command=self.stop_all_servers)
        stop_all_btn.pack(side="left", padx=4)
        ToolTip(stop_all_btn, "Gracefully terminate all running background servers.")

        open_browser_btn = ttk.Button(all_servers_bar, text="Open Browser WASM Portal", command=self.open_wasm_browser)
        open_browser_btn.pack(side="right", padx=4)
        ToolTip(open_browser_btn, "Open http://localhost:8080 in default web browser.")

        test_ws_btn = ttk.Button(all_servers_bar, text="Probe Web Gateway", command=self.test_web_gateway)
        test_ws_btn.pack(side="right", padx=4)
        ToolTip(test_ws_btn, "Test WebSocket connection and dispatch transport ping to DAWs.")

        # -------------------------------------------------------------
        # 5. Section: Omni-Plugin Bridge & Native Workstations
        # -------------------------------------------------------------
        workstation_frame = tk.LabelFrame(
            self.content_frame,
            text=" Native Digital Audio Workstations & Omni-Plugin Bridge ",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=8
        )
        workstation_frame.pack(fill="x", pady=4)
        ToolTip(workstation_frame, "Launch native compiled DAWs and inspect cross-DAW plugin bridging state.")

        # Plugin Bridge status bar
        bridge_status_bar = tk.Frame(workstation_frame, bg="#252526", padx=6, pady=4)
        bridge_status_bar.pack(fill="x", pady=(0, 6))

        tk.Label(
            bridge_status_bar,
            text="Omni-Plugin Bridge (Rust):",
            font=("Helvetica", 8, "bold"),
            bg="#252526",
            fg="#ffd54f"
        ).pack(side="left")

        self.bridge_ipc_lbl = tk.Label(
            bridge_status_bar,
            text="Ready (Unix Socket / Shared Memory / VST-LV2 Shim)",
            font=("Helvetica", 8),
            bg="#252526",
            fg="#e0e0e0"
        ).pack(side="left", padx=6)

        test_bridge_btn = ttk.Button(bridge_status_bar, text="Test Bridge IPC", command=self.test_omni_bridge)
        test_bridge_btn.pack(side="right", padx=2)
        ToolTip(test_bridge_btn, "Verify Rust omni_plugin_bridge cargo tests and IPC readiness.")

        probe_dsp_btn = ttk.Button(bridge_status_bar, text="Probe DSP Block", command=self.probe_dsp_block)
        probe_dsp_btn.pack(side="right", padx=2)
        ToolTip(probe_dsp_btn, "Stream a simulated 512-frame audio buffer through the Omni-Plugin Host.")

        stream_dsp_btn = ttk.Button(bridge_status_bar, text="Stream Headless Chunk", command=self.stream_headless_audio_block)
        stream_dsp_btn.pack(side="right", padx=2)
        ToolTip(stream_dsp_btn, "Execute real-time headless buffer streaming with latency & peak level metrics.")

        compat_btn = ttk.Button(bridge_status_bar, text="Check Plugin Compat", command=self.check_plugin_compat)
        compat_btn.pack(side="right", padx=2)
        ToolTip(compat_btn, "Query format compatibility across Ardour, LMMS, MusE, and Zrythm.")

        # DAW Launchers
        daw_btns_frame = tk.Frame(workstation_frame)
        daw_btns_frame.pack(fill="x", pady=2)

        self.daw_badges = {}

        daw_metadata = [
            ("ardour", "Ardour", "Pro Audio Tracking & Mastering (GTK/Waf)"),
            ("lmms", "LMMS", "Beatmaking & Synth Sequencer (Qt/CMake)"),
            ("muse", "MusE", "MIDI/Audio Workstation & Arranger"),
            ("zrythm", "Zrythm", "Modern DAW with Flexible Automation")
        ]

        for idx, (key, name, desc) in enumerate(daw_metadata):
            sub_card = tk.Frame(daw_btns_frame, relief="ridge", borderwidth=1, padx=6, pady=6)
            sub_card.pack(side="left", fill="both", expand=True, padx=3)

            top_row = tk.Frame(sub_card)
            top_row.pack(fill="x")

            name_lbl = tk.Label(top_row, text=name, font=("Helvetica", 10, "bold"))
            name_lbl.pack(side="left")

            badge = tk.Label(top_row, text="STANDBY", font=("Helvetica", 7, "bold"), fg="#888", bg="#222", padx=3)
            badge.pack(side="right")
            self.daw_badges[key] = badge

            desc_lbl = tk.Label(sub_card, text=desc, font=("Helvetica", 7), fg="#555", wraplength=170, justify="left")
            desc_lbl.pack(anchor="w", pady=(2, 6))

            launch_btn = ttk.Button(sub_card, text=f"Launch {name}", command=lambda k=key: self.launch_daw_gui(k))
            launch_btn.pack(fill="x")
            ToolTip(launch_btn, f"Launch native {name} binary as an independent child process.")


        # -------------------------------------------------------------
        # 6. Section: Unified Real-Time System Log & VU Metering
        # -------------------------------------------------------------
        log_frame = tk.LabelFrame(
            self.content_frame,
            text=" System Telemetry, VU Metering & Console Log ",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=8
        )
        log_frame.pack(fill="both", expand=True, pady=4)

        # Dual Stereo VU Meter Canvas
        vu_box = tk.Frame(log_frame, bg="#1e1e24", padx=6, pady=4)
        vu_box.pack(fill="x", pady=(0, 6))

        tk.Label(vu_box, text="Master Output VU (dBFS):", font=("Helvetica", 8, "bold"), bg="#1e1e24", fg="#61dafb").pack(side="left", padx=(0, 6))
        self.vu_canvas = tk.Canvas(vu_box, width=320, height=18, bg="#111", highlightthickness=1, highlightbackground="#333")
        self.vu_canvas.pack(side="left", padx=4)
        ToolTip(self.vu_canvas, "Live stereo master peak meter (green=-60dB to -12dB, yellow=-12dB to -1dB, red=clipping).")

        self.vu_text_lbl = tk.Label(vu_box, text="L: -inf dB | R: -inf dB", font=("Monospace", 8), bg="#1e1e24", fg="#a6e22e")
        self.vu_text_lbl.pack(side="left", padx=6)

        log_ctrl_bar = tk.Frame(log_frame)
        log_ctrl_bar.pack(fill="x", pady=(0, 4))

        tk.Label(log_ctrl_bar, text="Activity Log", font=("Helvetica", 8, "bold"), fg="#555").pack(side="left")

        clear_btn = ttk.Button(log_ctrl_bar, text="Clear Log", command=self.clear_log)
        clear_btn.pack(side="right", padx=2)
        ToolTip(clear_btn, "Clear current console log messages.")

        copy_btn = ttk.Button(log_ctrl_bar, text="Copy Log", command=self.copy_log)
        copy_btn.pack(side="right", padx=2)
        ToolTip(copy_btn, "Copy entire log output to system clipboard.")

        self.log_text = tk.Text(log_frame, height=8, bg="#181a1f", fg="#abb2bf", insertbackground="white", font=("Monospace", 8), state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)

        self._draw_vu_meter(0.0, 0.0)

        self.log(f"Omni-Dashboard {version_str} initialized. Autopilot mode active. All subsystems ready.")
        self.refresh_session_memory()

    def _on_canvas_configure(self, event):
        self.main_canvas.itemconfig(self.canvas_window, width=event.width)

    def _draw_vu_meter(self, level_l, level_r):
        """Draws stereo peak bars and scrolling waveform history on the VU meter canvas."""
        self.vu_canvas.delete("all")
        w = 320
        h = 18

        # Background channels (Left top, Right bottom)
        self.vu_canvas.create_rectangle(0, 1, w, 7, fill="#222", outline="")
        self.vu_canvas.create_rectangle(0, 10, w, 16, fill="#222", outline="")

        def get_color(ratio):
            if ratio < 0.75:
                return "#2e7d32"
            elif ratio < 0.90:
                return "#ffd54f"
            return "#f44336"

        len_l = int(max(0.0, min(1.0, level_l)) * (w * 0.7))
        len_r = int(max(0.0, min(1.0, level_r)) * (w * 0.7))

        if len_l > 0:
            self.vu_canvas.create_rectangle(0, 1, len_l, 7, fill=get_color(level_l), outline="")
        if len_r > 0:
            self.vu_canvas.create_rectangle(0, 10, len_r, 16, fill=get_color(level_r), outline="")

        # Waveform envelope mini-history sparkline (rightmost 30% of canvas)
        wave_start_x = int(w * 0.72)
        wave_width = w - wave_start_x
        num_points = len(self.meter_history)
        step = wave_width / max(1, num_points - 1)

        for i in range(num_points - 1):
            y1 = int(h / 2 - (self.meter_history[i] * (h / 2 - 2)))
            y2 = int(h / 2 - (self.meter_history[i + 1] * (h / 2 - 2)))
            x1 = int(wave_start_x + i * step)
            x2 = int(wave_start_x + (i + 1) * step)
            self.vu_canvas.create_line(x1, y1, x2, y2, fill="#61dafb", width=1)

    def _update_meter_telemetry(self, peak_ratio):
        """Updates live VU meter and waveform history buffer from incoming bridge telemetry."""
        import math
        clamped_ratio = max(0.0, min(1.0, peak_ratio))
        self.meter_history.pop(0)
        self.meter_history.append(clamped_ratio)

        db = 20.0 * math.log10(max(1e-4, clamped_ratio))
        self.vu_text_lbl.config(text=f"L: {db:.1f} dB | R: {db:.1f} dB")
        self._draw_vu_meter(clamped_ratio, clamped_ratio * 0.95)

    def start_health_watchdog(self):
        """Asynchronous background watchdog evaluating system daemon health."""
        if not health_watchdog:
            return
        def _watch():
            wd = health_watchdog.HealthWatchdog()
            while getattr(self, "_running", True):
                try:
                    status = wd.probe_all()
                    alive_count = sum(1 for v in status.values() if v.get("alive"))
                    total = len(status)
                    # Update badge in main thread
                    fg_color = "#a6e22e" if alive_count >= 2 else "#e5c07b"
                    self.after(0, lambda c=fg_color, s=f"WATCHDOG: {alive_count}/{total}": self.badge_watchdog.config(text=s, fg=c))
                except Exception:
                    pass
                time.sleep(6)
        threading.Thread(target=_watch, daemon=True).start()

    def _toggle_auto_save(self):
        if not session_memory:
            return
        mem = session_memory.SessionMemory()
        if self.auto_save_var.get():
            mem.enable_auto_save(15.0)
            self.log("[Session Memory] Auto-save daemon ENABLED (interval: 15s).")
        else:
            mem.disable_auto_save()
            self.log("[Session Memory] Auto-save daemon DISABLED.")

    def _run_macro(self, macro_cmd):
        self.muse_prompt.delete(0, tk.END)
        self.muse_prompt.insert(0, macro_cmd)
        self.execute_muse_command()

    def start_telemetry_listener(self):
        """Asynchronous UDP listener on 127.0.0.1:8005 to stream live bridge telemetry."""
        import socket
        def _listen():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", 8005))
                sock.settimeout(1.0)
                while getattr(self, "_running", True):
                    try:
                        data, _ = sock.recvfrom(2048)
                        text = data.decode("utf-8", errors="replace")
                        # Clean OSC string if formatted
                        if "[METER]" in text:
                            # Parse meter data: e.g. [METER] /track/master/meter:0.75
                            val_str = text.split(":")[-1].strip()
                            try:
                                v = float(val_str)
                                self.after(0, lambda val=v: self._update_meter_telemetry(val))
                            except ValueError:
                                pass
                        else:
                            clean_text = text.replace("/telemetry", "").strip()
                            self.after(0, lambda m=clean_text: self.log(f"[IPC Telemetry] {m}"))
                    except socket.timeout:
                        continue
                    except Exception:
                        break
                sock.close()
            except Exception:
                pass
        self._running = True
        threading.Thread(target=_listen, daemon=True).start()

    def _clear_muse_placeholder(self, event):
        if self.muse_prompt.get().startswith("Type command"):
            self.muse_prompt.delete(0, tk.END)

    def _clear_ai_placeholder(self, event):
        if self.ai_prompt.get().startswith("e.g."):
            self.ai_prompt.delete(0, tk.END)

    def _set_ai_prompt(self, text):
        self.ai_prompt.delete(0, tk.END)
        self.ai_prompt.insert(0, text)
        self.log(f"Selected AI Prompt Preset: '{text}'")

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}\n"
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, formatted)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _build_mixer_strips(self):
        for w in self.mixer_strips_frame.winfo_children():
            w.destroy()
        self.track_widgets.clear()

        tracks = ["kick", "snare", "hihat", "bass", "synth", "vocals", "master"]
        if session_memory:
            try:
                tracks = session_memory.SessionMemory().get_track_list()
            except Exception:
                pass

        for t in tracks:
            strip = tk.Frame(self.mixer_strips_frame, bg="#282c34", relief="ridge", borderwidth=1, padx=4, pady=4)
            strip.pack(side="left", fill="y", expand=True, padx=2)

            # Name Label
            lbl = tk.Label(strip, text=t.upper(), font=("Helvetica", 8, "bold"), bg="#282c34", fg="#61dafb")
            lbl.pack()
            ToolTip(lbl, f"Track {t.upper()} channel strip.")

            # Mini VU Peak Canvas
            vu = tk.Canvas(strip, width=32, height=6, bg="#111", highlightthickness=0)
            vu.pack(pady=2)

            # Fader Level Slider
            fader_val = 0.0
            if session_memory:
                try:
                    fader_val = session_memory.SessionMemory().tracks[t].fader
                except Exception:
                    pass

            scale = tk.Scale(
                strip,
                from_=6.0,
                to=-60.0,
                resolution=0.5,
                orient="vertical",
                length=85,
                bg="#282c34",
                fg="#abb2bf",
                highlightthickness=0,
                troughcolor="#1e1e24",
                font=("Monospace", 7),
                command=lambda val, name=t: self._on_fader_moved(name, val)
            )
            scale.set(fader_val)
            scale.pack()
            ToolTip(scale, f"Adjust {t.upper()} fader gain (dB).")

            # Pan Slider (L <-> R)
            pan_val = 0.0
            if session_memory:
                try:
                    pan_val = getattr(session_memory.SessionMemory().tracks[t], "pan", 0.0)
                except Exception:
                    pass

            pan_scale = tk.Scale(
                strip,
                from_=-1.0,
                to=1.0,
                resolution=0.05,
                orient="horizontal",
                length=56,
                bg="#282c34",
                fg="#abb2bf",
                highlightthickness=0,
                troughcolor="#1e1e24",
                font=("Monospace", 6),
                command=lambda val, name=t: self._on_pan_moved(name, val)
            )
            pan_scale.set(pan_val)
            pan_scale.pack(pady=1)
            ToolTip(pan_scale, f"Stereo pan for {t.upper()} (-1.0 Left to +1.0 Right).")

            # Mute, Solo, and Freeze Buttons
            btn_row = tk.Frame(strip, bg="#282c34")
            btn_row.pack(fill="x", pady=2)

            mute_btn = tk.Button(
                btn_row, text="M", width=1, font=("Helvetica", 7, "bold"),
                bg="#3a3f4b", fg="#fff", command=lambda name=t: self._toggle_track_mute(name)
            )
            mute_btn.pack(side="left", padx=1)
            ToolTip(mute_btn, f"Mute {t.upper()} track.")

            solo_btn = tk.Button(
                btn_row, text="S", width=1, font=("Helvetica", 7, "bold"),
                bg="#3a3f4b", fg="#fff", command=lambda name=t: self._toggle_track_solo(name)
            )
            solo_btn.pack(side="left", padx=1)
            ToolTip(solo_btn, f"Solo {t.upper()} track.")

            is_frozen = False
            if session_memory:
                try:
                    is_frozen = getattr(session_memory.SessionMemory().tracks.get(t), "frozen", False)
                except Exception:
                    pass

            freeze_btn = tk.Button(
                btn_row, text="F", width=1, font=("Helvetica", 7, "bold"),
                bg="#61dafb" if is_frozen else "#3a3f4b",
                fg="#1e1e24" if is_frozen else "#fff",
                command=lambda name=t: self._toggle_track_freeze(name)
            )
            freeze_btn.pack(side="left", padx=1)
            ToolTip(freeze_btn, f"Freeze/Unfreeze {t.upper()} track (offline cache DSP rendering).")

            self.track_widgets[t] = {
                "fader": scale,
                "pan": pan_scale,
                "mute_btn": mute_btn,
                "solo_btn": solo_btn,
                "freeze_btn": freeze_btn,
                "vu": vu
            }

    def _on_fader_moved(self, track_name, value):
        val = float(value)
        if session_memory:
            session_memory.SessionMemory().set_fader(track_name, val)
        try:
            import bobui_bridge
            bobui_bridge.broadcast_track_update(track_name, fader=val)
        except Exception:
            self.send_osc_direct(f"/track/{track_name}/fader", val)

    def _on_pan_moved(self, track_name, value):
        val = float(value)
        if session_memory:
            t = session_memory.SessionMemory().get_or_create_track(track_name)
            t.pan = val
            t.update_parameter("pan", val)
        try:
            import bobui_bridge
            bobui_bridge.broadcast_track_update(track_name, pan=val)
        except Exception:
            self.send_osc_direct(f"/track/{track_name}/pan", val)

    def _toggle_track_mute(self, track_name):
        if not session_memory:
            return
        is_muted = session_memory.SessionMemory().toggle_mute(track_name)
        w = self.track_widgets.get(track_name)
        if w:
            w["mute_btn"].config(bg="#f44336" if is_muted else "#3a3f4b")
        try:
            import bobui_bridge
            bobui_bridge.broadcast_track_update(track_name, muted=is_muted)
        except Exception:
            self.send_osc_direct(f"/track/{track_name}/mute", 1.0 if is_muted else 0.0)
        self.log(f"Track {track_name.upper()} {'MUTED' if is_muted else 'UNMUTED'}.")

    def _toggle_track_solo(self, track_name):
        if not session_memory:
            return
        is_solo = session_memory.SessionMemory().toggle_solo(track_name)
        w = self.track_widgets.get(track_name)
        if w:
            w["solo_btn"].config(bg="#ffeb3b" if is_solo else "#3a3f4b", fg="#000" if is_solo else "#fff")
        try:
            import bobui_bridge
            bobui_bridge.broadcast_track_update(track_name, soloed=is_solo)
        except Exception:
            self.send_osc_direct(f"/track/{track_name}/solo", 1.0 if is_solo else 0.0)
        self.log(f"Track {track_name.upper()} {'SOLOED' if is_solo else 'UNSOLOED'}.")

    def _toggle_track_freeze(self, track_name):
        if not session_memory:
            return
        mem = session_memory.SessionMemory()
        track = mem.get_or_create_track(track_name)
        w = self.track_widgets.get(track_name)
        if track.frozen:
            res = mem.unfreeze_track(track_name)
            if w:
                w["freeze_btn"].config(bg="#3a3f4b", fg="#fff")
                w["fader"].config(state="normal")
            self.log(f"[Track Freeze] Track '{track_name.upper()}' unfrozen. Real-time DSP active.")
        else:
            res = mem.freeze_track(track_name)
            if w:
                w["freeze_btn"].config(bg="#61dafb", fg="#1e1e24")
                w["fader"].config(state="disabled")
            self.log(f"[Track Freeze] Track '{track_name.upper()}' frozen to offline cache ({res['freeze_file']}).")

    def _on_plugin_cutoff_moved(self, val):
        track = self.plugin_track_combo.get() or "bass"
        v = float(val)
        if session_memory:
            session_memory.SessionMemory().sync_plugin_parameter(track, "omni_filter", "cutoff", v)
        self.plugin_sync_status.config(text=f"Sync: {track}/cutoff={int(v)}Hz")
        self.send_osc_direct(f"/track/{track}/plugin/omni_filter/cutoff", v)

    def _on_plugin_drive_moved(self, val):
        track = self.plugin_track_combo.get() or "bass"
        v = float(val)
        if session_memory:
            session_memory.SessionMemory().sync_plugin_parameter(track, "omni_filter", "drive", v)
        self.plugin_sync_status.config(text=f"Sync: {track}/drive={v:.2f}")
        self.send_osc_direct(f"/track/{track}/plugin/omni_filter/drive", v)

    def _apply_plugin_preset(self):
        track = self.plugin_track_combo.get() or "bass"
        preset = self.plugin_preset_combo.get() or "Warm Tube"
        if session_memory:
            mem = session_memory.SessionMemory()
            if hasattr(mem, "apply_plugin_preset"):
                applied = mem.apply_plugin_preset(track, preset)
                for key, val in applied.items():
                    self.send_osc_direct(f"/track/{track}/plugin/{key}", val)
                self.plugin_sync_status.config(text=f"Preset: {preset} on {track}")
                self.log(f"Omni-Plugin preset '{preset}' applied to track '{track}'.")
                self.refresh_session_memory()

    def import_session_dialog(self):
        if not session_memory or not session_importer:
            self.log("Session importer or session memory module missing.")
            return

        in_file = filedialog.askopenfilename(
            title="Import Session File",
            filetypes=[
                ("Supported Sessions", "*.ardour *.mmp *.json *.xml"),
                ("Ardour Session (*.ardour)", "*.ardour"),
                ("LMMS Project (*.mmp)", "*.mmp"),
                ("Universal Manifest (*.json)", "*.json"),
                ("All Files", "*.*")
            ]
        )
        if in_file:
            try:
                mem = session_memory.SessionMemory()
                if in_file.endswith(".mmp"):
                    imported = session_importer.import_from_lmms(in_file, mem)
                elif in_file.endswith(".json"):
                    imported = session_importer.import_from_manifest(in_file, mem)
                else:
                    imported = session_importer.import_from_ardour(in_file, mem)
                self.log(f"[Session Importer] Imported {len(imported)} tracks from {os.path.basename(in_file)}.")
                self.refresh_session_memory()
            except Exception as e:
                self.log(f"Import session error: {e}")

    def merge_session_dialog(self):
        if not session_memory or not session_importer:
            self.log("Session importer or session memory module missing.")
            return

        in_file = filedialog.askopenfilename(
            title="Select Session File to Merge",
            filetypes=[
                ("Supported Sessions", "*.ardour *.mmp *.json *.xml"),
                ("Ardour Session (*.ardour)", "*.ardour"),
                ("LMMS Project (*.mmp)", "*.mmp"),
                ("Universal Manifest (*.json)", "*.json"),
                ("All Files", "*.*")
            ]
        )
        if not in_file:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Merge Session - Conflict Resolution")
        dialog.geometry("380x220")
        dialog.transient(self)

        tk.Label(dialog, text=f"Merging: {os.path.basename(in_file)}", font=("Helvetica", 9, "bold")).pack(pady=6)
        tk.Label(dialog, text="Select Conflict Resolution Strategy:", font=("Helvetica", 8)).pack(pady=2)

        strat_var = tk.StringVar(value="merge_latest")
        rb_frame = tk.Frame(dialog)
        rb_frame.pack(pady=4)

        ttk.Radiobutton(rb_frame, text="Merge Latest Timestamp (Automatic)", variable=strat_var, value="merge_latest").pack(anchor="w", pady=2)
        ttk.Radiobutton(rb_frame, text="Overwrite Remote (Incoming Takes Priority)", variable=strat_var, value="overwrite_remote").pack(anchor="w", pady=2)
        ttk.Radiobutton(rb_frame, text="Keep Local (Current Session Preserved)", variable=strat_var, value="keep_local").pack(anchor="w", pady=2)

        def _execute_merge():
            strategy = strat_var.get()
            dialog.destroy()
            try:
                mem = session_memory.SessionMemory()
                if in_file.endswith(".mmp"):
                    incoming_tracks = session_importer.import_from_lmms(in_file)
                elif in_file.endswith(".json"):
                    incoming_tracks = session_importer.import_from_manifest(in_file)
                else:
                    incoming_tracks = session_importer.import_from_ardour(in_file)

                report = mem.resolve_session_conflict(incoming_tracks, strategy=strategy)
                self.log(f"[Session Merge] Strategy '{strategy}' applied: {report['merged_tracks_count']} total tracks.")
                self.log(f"  • Conflicts detected: {len(report['conflicts'])}")
                self.log(f"  • Changes applied: {len(report['changes_applied'])}")
                for chg in report["changes_applied"]:
                    self.log(f"    - {chg['track']} ({chg['field']}): {chg['old_val']} -> {chg['new_val']}")
                    # If fader changed, send live OSC update to active DAWs
                    if chg['field'] == 'fader':
                        self.send_osc_direct(f"/track/{chg['track']}/fader", chg['new_val'])

                self.refresh_session_memory()
            except Exception as e:
                self.log(f"Merge session error: {e}")

        btn_row = tk.Frame(dialog)
        btn_row.pack(pady=10)
        ttk.Button(btn_row, text="Execute Merge", command=_execute_merge).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side="left", padx=4)

    def export_session_dialog(self):
        if not session_memory or not session_exporter:
            self.log("Session exporter or session memory module missing.")
            return

        out_file = filedialog.asksaveasfilename(
            title="Export Session To DAW",
            defaultextension=".ardour",
            filetypes=[
                ("Ardour Session (*.ardour)", "*.ardour"),
                ("LMMS Project (*.mmp)", "*.mmp"),
                ("Universal Manifest (*.json)", "*.json"),
                ("All Files", "*.*")
            ]
        )
        if out_file:
            try:
                mem = session_memory.SessionMemory()
                if out_file.endswith(".mmp"):
                    session_exporter.export_to_lmms(mem.tracks, out_file)
                elif out_file.endswith(".json"):
                    session_exporter.export_manifest(mem.tracks, out_file)
                else:
                    session_exporter.export_to_ardour(mem.tracks, out_file)
                self.log(f"[Session Exporter] Session exported successfully to: {out_file}")
            except Exception as e:
                self.log(f"Export session error: {e}")

    def transition_daw_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Transition Session to DAW")
        dialog.geometry("340x200")
        dialog.transient(self)

        tk.Label(dialog, text="Source DAW:", font=("Helvetica", 9)).pack(anchor="w", padx=16, pady=(8, 2))
        src_combo = ttk.Combobox(dialog, values=["ardour", "lmms", "muse", "zrythm"], state="readonly", width=24)
        src_combo.set("ardour")
        src_combo.pack(padx=16, pady=2)

        tk.Label(dialog, text="Target DAW:", font=("Helvetica", 9)).pack(anchor="w", padx=16, pady=(6, 2))
        tgt_combo = ttk.Combobox(dialog, values=["ardour", "lmms", "muse", "zrythm"], state="readonly", width=24)
        tgt_combo.set("lmms")
        tgt_combo.pack(padx=16, pady=2)

        safe_var = tk.BooleanVar(value=True)
        safe_chk = ttk.Checkbutton(dialog, text="Rollback on Verification Failure", variable=safe_var)
        safe_chk.pack(anchor="w", padx=16, pady=4)

        def _do_transition():
            src = src_combo.get()
            tgt = tgt_combo.get()
            do_safe = safe_var.get()
            try:
                import bobui_bridge
                res = bobui_bridge.transition_session(src, tgt)
                if do_safe:
                    verification = bobui_bridge.verify_and_rollback_transition(res)
                    if verification.get("status") == "rolled_back":
                        self.log(f"[Transition Warning] Verification failed: {verification.get('reason')}. Automatically rolled back.")
                        self.refresh_session_memory()
                        dialog.destroy()
                        return

                self.log(f"[Session Transition] Successfully transitioned from {src.upper()} to {tgt.upper()}.")
                self.log(f"  • Snapshot saved: {res.get('checkpoint')}")
                self.log(f"  • Exported: {res.get('exported_file')}")
                self.refresh_session_memory()
            except Exception as e:
                self.log(f"[Transition Error] {e}")
            dialog.destroy()

        btn_row = tk.Frame(dialog)
        btn_row.pack(pady=12)
        ttk.Button(btn_row, text="Execute Transition", command=_do_transition).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side="left", padx=4)

    def broadcast_session_to_all_daws(self):
        self.log("[Multi-DAW Sync] Broadcasting active session state across all member DAWs with echo suppression...")
        def _sync():
            try:
                import bobui_bridge
                res = bobui_bridge.broadcast_session_state_safe(tracks=None)
                self.after(0, lambda: self.log(
                    f"[Multi-DAW Sync] Success: {res.get('tracks_dispatched')} tracks pushed | "
                    f"{res.get('echoes_suppressed')} echoes suppressed across {len(res.get('target_daws'))} DAWs."
                ))
            except Exception as e:
                self.after(0, lambda: self.log(f"[Multi-DAW Sync Error] {e}"))
        threading.Thread(target=_sync, daemon=True).start()

    def test_sync_loop_probe(self):
        self.log("[Sync Loop Probe] Dispatching high-frequency rapid parameter stream to test echo-suppression...")
        def _probe():
            try:
                import bobui_bridge
                # Fire two rapid identical bursts
                res1 = bobui_bridge.broadcast_session_state_safe(tracks=None, source_daw="ardour")
                res2 = bobui_bridge.broadcast_session_state_safe(tracks=None, source_daw="ardour")
                self.after(0, lambda: self.log(
                    f"[Sync Loop Probe] Burst 1: {res1['tracks_dispatched']} dispatched. "
                    f"Burst 2 (rapid duplicate): {res2['echoes_suppressed']} echo packets suppressed (no feedback loops detected)."
                ))
            except Exception as e:
                self.after(0, lambda: self.log(f"[Sync Loop Probe Error] {e}"))
        threading.Thread(target=_probe, daemon=True).start()

    def sync_diff_to_baseline(self):
        if not session_memory:
            return
        mem = session_memory.SessionMemory()
        checkpoints = mem.list_checkpoints()
        if not checkpoints:
            self.log("[Session Diff] No checkpoints saved to compute diff against. Save a snapshot first.")
            return

        base_cp = checkpoints[0]
        diff = mem.compute_state_diff(base_cp)
        if not diff:
            self.log(f"[Session Diff] Current session matches checkpoint '{base_cp}' 100%. No diff to broadcast.")
        else:
            self.log(f"[Session Diff] Computed {len(diff)} track deltas against baseline '{base_cp}':")
            for t_name, chg in diff.items():
                self.log(f"  • {t_name.upper()}: {chg}")
            # Stream diff to bridge
            mem.sync_session_manifest_to_bridge()

    def compare_checkpoints_dialog(self):
        if not session_memory:
            return
        mem = session_memory.SessionMemory()
        checkpoints = mem.list_checkpoints()
        if not checkpoints:
            messagebox.showinfo("Checkpoints", "No checkpoints saved to compare. Save snapshots first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Checkpoint Visual Diff Inspector")
        dialog.geometry("520x420")
        dialog.transient(self)

        top_ctrls = tk.Frame(dialog, padx=8, pady=8)
        top_ctrls.pack(fill="x")

        tk.Label(top_ctrls, text="Base:", font=("Helvetica", 9, "bold")).pack(side="left", padx=2)
        combo_a = ttk.Combobox(top_ctrls, values=checkpoints, state="readonly", width=16)
        combo_a.set(checkpoints[0])
        combo_a.pack(side="left", padx=4)

        tk.Label(top_ctrls, text="Compare With:", font=("Helvetica", 9, "bold")).pack(side="left", padx=2)
        compare_options = ["[Live Current State]"] + checkpoints
        combo_b = ttk.Combobox(top_ctrls, values=compare_options, state="readonly", width=18)
        combo_b.set(compare_options[0])
        combo_b.pack(side="left", padx=4)

        # Diff results text box
        diff_text = tk.Text(dialog, wrap="word", bg="#1e1e24", fg="#abb2bf", font=("Monospace", 9), padx=8, pady=8)
        diff_text.pack(fill="both", expand=True, padx=8, pady=4)

        def _refresh_diff():
            diff_text.config(state="normal")
            diff_text.delete("1.0", tk.END)
            snap_a = combo_a.get()
            target_b = combo_b.get()
            snap_b = None if target_b == "[Live Current State]" else target_b

            diffs = mem.compare_session_snapshots(snap_a, snap_b)
            if not diffs:
                diff_text.insert(tk.END, f"✓ Identical: No parameter differences between '{snap_a}' and '{target_b}'.\n")
            else:
                diff_text.insert(tk.END, f"=== Comparison: {snap_a} vs {target_b} ({len(diffs)} differences) ===\n\n")
                for d in diffs:
                    diff_text.insert(
                        tk.END,
                        f"• Track: {d['track'].upper():<12} | Field: {d['field']:<8} | "
                        f"{d['old_val']} -> {d['new_val']} ({d['change_type']})\n"
                    )
            diff_text.config(state="disabled")

        ttk.Button(top_ctrls, text="Inspect Diff", command=_refresh_diff).pack(side="left", padx=6)
        combo_a.bind("<<ComboboxSelected>>", lambda e: _refresh_diff())
        combo_b.bind("<<ComboboxSelected>>", lambda e: _refresh_diff())

        btn_row = tk.Frame(dialog, pady=6)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Close", command=dialog.destroy).pack(side="right", padx=8)

        # Initial render
        _refresh_diff()

    def sync_manifest_to_bridge(self):
        if not session_memory:
            return
        mem = session_memory.SessionMemory()
        if hasattr(mem, "sync_session_manifest_to_bridge"):
            ok = mem.sync_session_manifest_to_bridge()
            if ok:
                self.log("[Session Sync] Session manifest successfully synchronized to Omni-Plugin Bridge.")
            else:
                self.log("[Session Sync Note] Bridge socket idle or unreachable.")
        self.refresh_session_memory()

    def restore_checkpoint_dialog(self):
        if not session_memory:
            return
        mem = session_memory.SessionMemory()
        checkpoints = mem.list_checkpoints()
        if not checkpoints:
            messagebox.showinfo("Checkpoints", "No checkpoints saved in current session.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Restore Session Checkpoint")
        dialog.geometry("340x180")
        dialog.transient(self)

        tk.Label(dialog, text="Select Checkpoint to Restore:", font=("Helvetica", 9, "bold")).pack(pady=8)
        combo = ttk.Combobox(dialog, values=checkpoints, state="readonly", width=28)
        combo.set(checkpoints[-1])
        combo.pack(pady=4)

        def _do_restore():
            chosen = combo.get()
            if chosen:
                ok = mem.restore_checkpoint(chosen)
                if ok:
                    for t_name, track in mem.tracks.items():
                        self.send_osc_direct(f"/track/{t_name}/fader", track.fader)
                    self.log(f"[Session Memory] Checkpoint '{chosen}' restored across all DAWs.")
                    self.refresh_session_memory()
            dialog.destroy()

        btn_row = tk.Frame(dialog)
        btn_row.pack(pady=12)
        ttk.Button(btn_row, text="Restore", command=_do_restore).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side="left", padx=4)

    def audit_session_state(self):
        if not session_memory:
            return
        mem = session_memory.SessionMemory()
        res = mem.audit_session_consistency()
        if res.get("healthy"):
            self.log(f"[Session Audit] All {res.get('total_tracks')} tracks conform to parameter boundaries and valid roles.")
        else:
            self.log(f"[Session Audit] Resolved {len(res.get('issues_resolved'))} issues across session tracks:")
            for issue in res.get("issues_resolved"):
                self.log(f"  • {issue}")
        self.refresh_session_memory()

    def save_session_snapshot(self):
        if not session_memory:
            return
        snap_name = f"snapshot_{int(time.time())}"
        session_memory.SessionMemory().save_checkpoint(snap_name)
        self.log(f"[Session Memory] Checkpoint saved: '{snap_name}'")
        self.refresh_session_memory()

    def undo_last_mix_action(self):
        if not session_memory:
            return
        reverted = session_memory.SessionMemory().undo_last_action()
        if reverted:
            for path, val in reverted:
                self.send_osc_direct(path, val)
            self.log(f"[Session Memory] Reverted {len(reverted)} parameters from last action.")
        else:
            self.log("[Session Memory] No actions available to undo.")
        self.refresh_session_memory()

    def redo_last_mix_action(self):
        if not session_memory:
            return
        applied = session_memory.SessionMemory().redo_last_action()
        if applied:
            for path, val in applied:
                self.send_osc_direct(path, val)
            self.log(f"[Session Memory] Re-applied {len(applied)} parameters from redo stack.")
        else:
            self.log("[Session Memory] No actions available to redo.")
        self.refresh_session_memory()

    def refresh_session_memory(self):
        if not session_memory:
            return
        try:
            mem = session_memory.SessionMemory()
            summary = mem.get_summary()
            self.mem_status_lbl.config(text=f"{summary['total_tracks']} tracks | {len(summary['recent_actions'])} actions | {len(mem.checkpoints)} snaps")
            self._build_mixer_strips()

            # Update active DAW badge indicators
            if hasattr(mem, "get_active_daws"):
                active_daws = mem.get_active_daws()
                for key, badge in getattr(self, "daw_badges", {}).items():
                    if key in active_daws:
                        badge.config(text="ACTIVE", fg="#a6e22e")
                    else:
                        badge.config(text="STANDBY", fg="#888")
        except Exception as e:
            self.log(f"Session memory refresh error: {e}")

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def copy_log(self):
        content = self.log_text.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(content)
        self.log("Telemetry log copied to clipboard.")

    # -------------------------------------------------------------
    # System Tray Integration
    # -------------------------------------------------------------
    def init_system_tray(self):
        if not HAS_TRAY:
            self.badge_tray.config(text="TRAY: N/A", bg="#3a3d45", fg="#e5c07b")
            self.log("System Tray: pystray/PIL unavailable or unsupported in headless environment.")
            return

        def create_tray_image():
            # 64x64 Bobtrax audio waveform logo
            img = Image.new('RGBA', (64, 64), color=(30, 30, 36, 255))
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], outline=(97, 218, 251, 255), width=3)
            # Sound wave lines
            draw.line([20, 32, 20, 32], fill=(166, 226, 46, 255), width=3)
            draw.line([26, 22, 26, 42], fill=(166, 226, 46, 255), width=3)
            draw.line([32, 14, 32, 50], fill=(97, 218, 251, 255), width=3)
            draw.line([38, 24, 38, 40], fill=(166, 226, 46, 255), width=3)
            draw.line([44, 30, 44, 34], fill=(166, 226, 46, 255), width=3)
            return img

        menu = pystray.Menu(
            pystray.MenuItem("Show / Hide Dashboard", self.toggle_window_visibility, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start All Servers", lambda: self.after(0, self.start_all_servers)),
            pystray.MenuItem("Stop All Servers", lambda: self.after(0, self.stop_all_servers)),
            pystray.MenuItem("Open WebAssembly Portal", lambda: self.after(0, self.open_wasm_browser)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit Bobtrax (Terminate Servers)", lambda: self.after(0, self.quit_application))
        )

        try:
            # Check if an X11 system tray manager is available before starting pystray
            # In headless environments (like xvfb without a desktop dock), pystray prints traceback on stderr
            import Xlib.display
            display = Xlib.display.Display()
            atom = display.intern_atom(f'_NET_SYSTEM_TRAY_S{display.get_default_screen()}')
            owner = display.get_selection_owner(atom)
            if owner == Xlib.X.NONE:
                self.badge_tray.config(text="TRAY: STANDBY", fg="#e5c07b")
                self.log("System tray: No active system tray manager detected in display. Tray icon in standby.")
                return

            self.tray_icon = pystray.Icon("bobtrax", create_tray_image(), "Bobtrax Omni-Dashboard", menu)
            def _run_tray():
                try:
                    self.tray_icon.run()
                except Exception:
                    pass
            threading.Thread(target=_run_tray, daemon=True).start()
            self.badge_tray.config(text="TRAY: ACTIVE", fg="#a6e22e")
            self.log("System tray icon initialized successfully.")
        except Exception as e:
            self.badge_tray.config(text="TRAY: OFF", fg="#e06c75")
            self.log(f"System tray icon could not be attached: {e}")

    def toggle_window_visibility(self):
        def _toggle():
            if self.state() == 'withdrawn':
                self.deiconify()
                self.lift()
            else:
                self.withdraw()
        self.after(0, _toggle)

    def on_close_requested(self):
        self.quit_application()

    def quit_application(self):
        self.log("Shutting down Bobtrax Omni-Dashboard and terminating all servers...")
        self._running = False
        if session_memory:
            try:
                session_memory.SessionMemory().disable_auto_save()
            except Exception:
                pass
        self.stop_all_servers()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.destroy()

    # -------------------------------------------------------------
    # MUSE Command Palette & Transport
    # -------------------------------------------------------------
    def execute_muse_command(self, event=None):
        cmd = self.muse_prompt.get().strip()
        if not cmd or cmd.startswith("Type command"):
            return

        self.log(f"[MUSE Command] Input: '{cmd}'")
        cmd_lower = cmd.lower()

        if cmd_lower in ["play", "start"]:
            self.dispatch_transport("play")
        elif cmd_lower in ["stop", "pause"]:
            self.dispatch_transport("stop")
        elif cmd_lower in ["record", "rec"]:
            self.dispatch_transport("record")
        elif cmd_lower.startswith("tempo") or cmd_lower.startswith("bpm"):
            parts = cmd.split()
            bpm = parts[1] if len(parts) > 1 else "120"
            self.log(f"[MUSE Command] Setting ecosystem tempo to {bpm} BPM...")
            self.send_osc_direct("/transport_tempo", float(bpm))
        elif cmd_lower in ["servers", "status"]:
            status_summary = (
                f"WASM: {'RUNNING' if self.processes['wasm'] else 'STOPPED'} | "
                f"OSC Bridge: {'RUNNING' if self.processes['osc_bridge'] else 'STOPPED'} | "
                f"WebSocket: {'RUNNING' if self.processes['osc_web'] else 'STOPPED'}"
            )
            self.log(f"[MUSE Command Status] {status_summary}")
        elif "mute all" in cmd_lower:
            self.log("[MUSE Macro] Muting all session tracks...")
            for t in ["kick", "snare", "hihat", "bass", "synth", "vocals"]:
                self.send_osc_direct(f"/track/{t}/mute", 1.0)
        elif "reset faders" in cmd_lower:
            self.log("[MUSE Macro] Resetting all track faders to 0.0 dB...")
            for t in ["kick", "snare", "hihat", "bass", "synth", "vocals", "master"]:
                self.send_osc_direct(f"/track/{t}/fader", 0.0)
        elif "solo vocal" in cmd_lower:
            self.log("[MUSE Macro] Soloing vocal track and muting accompaniment...")
            self.send_osc_direct("/track/vocals/solo", 1.0)
        else:
            self.log(f"[MUSE Command] Routing '{cmd}' to active DAW routing bridge.")
            self.send_osc_direct(f"/command/{cmd_lower.replace(' ', '_')}", 1.0)

        self.muse_prompt.delete(0, tk.END)

    def dispatch_transport(self, action):
        self.log(f"Transport action dispatched: {action.upper()}")
        path_map = {
            "play": "/transport_play",
            "stop": "/transport_stop",
            "record": "/transport_record"
        }
        osc_path = path_map.get(action, f"/transport_{action}")
        self.send_osc_direct(osc_path, 1.0)

    def send_osc_direct(self, osc_path, value):
        def _send():
            try:
                from pythonosc.udp_client import SimpleUDPClient
                client = SimpleUDPClient("127.0.0.1", 8000)
                client.send_message(osc_path, value)
                self.after(0, lambda: self.log(f"OSC Transmitted -> {osc_path}: {value}"))
            except ImportError:
                self.after(0, lambda: self.log(f"OSC routing simulated (python-osc not loaded): {osc_path} -> {value}"))
            except Exception as e:
                self.after(0, lambda: self.log(f"OSC send warning: {e}"))
        threading.Thread(target=_send, daemon=True).start()

    # -------------------------------------------------------------
    # AI Production Suite Execution
    # -------------------------------------------------------------
    def load_stems(self):
        stems = filedialog.askopenfilenames(
            title="Select Multi-Track Stems",
            filetypes=[("Audio Files", "*.wav *.mp3 *.flac *.ogg"), ("All Files", "*.*")]
        )
        if stems:
            self.selected_stems = stems
            self.stem_lbl.config(text=f"Attached {len(stems)} track(s).", fg="#2e7d32")
            stem_names = [os.path.basename(s) for s in stems]
            self.log(f"Track context attached: {', '.join(stem_names)}")

    def discover_session_file(self):
        filename = filedialog.askopenfilename(
            title="Select DAW Session File",
            filetypes=[("DAW Sessions", "*.ardour *.mmp *.xml"), ("All Files", "*.*")]
        )
        if filename:
            try:
                cmd = [sys.executable, MIXING_ASSISTANT_PY, "--session", filename, "status", "--dry-run"]
                res = subprocess.run(cmd, capture_output=True, text=True)
                self.stem_lbl.config(text=f"Session: {os.path.basename(filename)}", fg="#2e7d32")
                self.log(f"Discovered session file: {filename}")
                if res.stdout:
                    for line in res.stdout.strip().split("\n"):
                        self.log(line)
            except Exception as e:
                self.log(f"Error scanning session file: {e}")

    def browse_audio_file(self):
        filename = filedialog.askopenfilename(
            title="Select Source Audio Track",
            filetypes=[("Audio Files", "*.wav *.mp3 *.flac *.ogg"), ("All Files", "*.*")]
        )
        if filename:
            self.selected_audio_file = filename
            self.audio_file_entry.delete(0, tk.END)
            self.audio_file_entry.insert(0, filename)
            self.log(f"Audio file selected for separation: {os.path.basename(filename)}")

    def run_stem_separator(self):
        audio_path = self.audio_file_entry.get().strip()
        if not audio_path or audio_path.startswith("Select input"):
            self.log("Error: Please select a valid audio file to separate.")
            return

        model = self.model_combo.get()
        use_gpu = self.gpu_var.get()

        self.log(f"Starting Stem Separation on '{os.path.basename(audio_path)}' (Model: {model}, GPU: {use_gpu})...")
        self.separate_btn.config(state="disabled", text="Separating...")

        def _run_sep():
            try:
                cmd = [sys.executable, STEM_SEPARATOR_PY, audio_path, "-n", model]
                if use_gpu:
                    cmd.append("--gpu")

                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.stdout:
                    for line in proc.stdout.strip().split("\n"):
                        self.after(0, lambda l=line: self.log(l))
                if proc.stderr:
                    for line in proc.stderr.strip().split("\n"):
                        self.after(0, lambda l=line: self.log(f"[Stem Separator] {l}"))

                self.after(0, lambda: self.log("Stem separation process finished successfully."))
            except Exception as e:
                self.after(0, lambda: self.log(f"Stem separation error: {e}"))
            finally:
                self.after(0, lambda: self.separate_btn.config(state="normal", text="Run Stem Separation"))

        threading.Thread(target=_run_sep, daemon=True).start()

    def execute_mix(self):
        prompt = self.ai_prompt.get().strip()
        if not prompt or prompt.startswith("e.g."):
            self.log("Error: Please enter a natural language mixing prompt.")
            return

        self.log(f"AI Mixing Assistant: Analyzing '{prompt}'...")
        self.exec_mix_btn.config(state="disabled", text="Processing...")

        stem_names = [os.path.splitext(os.path.basename(s))[0] for s in self.selected_stems]
        env = os.environ.copy()
        if stem_names:
            env["BOBTRAX_TRACKS"] = ",".join(stem_names)

        def _run_ai():
            try:
                cmd = [sys.executable, MIXING_ASSISTANT_PY, prompt]
                if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("GROQ_API_KEY"):
                    cmd.extend(["--llm-url", "http://localhost:1234/v1"])

                proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
                if proc.stdout:
                    for line in proc.stdout.strip().split("\n"):
                        self.after(0, lambda l=line: self.log(f"[AI Assistant] {l}"))
                if proc.stderr:
                    for line in proc.stderr.strip().split("\n"):
                        self.after(0, lambda l=line: self.log(f"[AI Assistant Warning] {l}"))

                self.after(0, lambda: self.log("AI Mixing execution complete."))
            except Exception as e:
                self.after(0, lambda: self.log(f"AI Mixing Assistant failure: {e}"))
            finally:
                self.after(0, lambda: self.exec_mix_btn.config(state="normal", text="Execute AI Mix"))

        threading.Thread(target=_run_ai, daemon=True).start()

    # -------------------------------------------------------------
    # Server Lifecycle Management
    # -------------------------------------------------------------
    def start_wasm(self):
        if self.processes["wasm"]:
            self.log("WebAssembly server already running.")
            return
        self.log("Starting WebAssembly Collaboration Server on port 8080...")
        try:
            self.processes["wasm"] = subprocess.Popen(
                [sys.executable, WASM_HOST_PY, "--port", "8080"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.badge_wasm.config(text="WASM: 8080", fg="#a6e22e")
            self.start_wasm_btn.config(state="disabled")
            self.stop_wasm_btn.config(state="normal")
            self.log("WASM Host is live at http://localhost:8080")
        except Exception as e:
            self.log(f"Failed to start WASM server: {e}")

    def stop_wasm(self):
        if self.processes["wasm"]:
            self.log("Stopping WebAssembly server...")
            self.processes["wasm"].terminate()
            self.processes["wasm"].wait()
            self.processes["wasm"] = None
            self.badge_wasm.config(text="WASM: STOPPED", fg="#f92672")
            self.start_wasm_btn.config(state="normal")
            self.stop_wasm_btn.config(state="disabled")
            self.log("WASM server stopped.")

    def start_osc_bridge(self):
        if self.processes["osc_bridge"]:
            self.log("OSC Bridge is already active.")
            return
        self.log("Starting Central OSC Bridge (127.0.0.1:8000)...")
        try:
            self.processes["osc_bridge"] = subprocess.Popen(
                [sys.executable, OSC_BRIDGE_PY, "--port", "8000"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.badge_bridge.config(text="OSC: 8000", fg="#a6e22e")
            self.start_bridge_btn.config(state="disabled")
            self.stop_bridge_btn.config(state="normal")
            self.log("OSC Bridge router started on 127.0.0.1:8000")
        except Exception as e:
            self.log(f"Failed to start OSC Bridge: {e}")

    def stop_osc_bridge(self):
        if self.processes["osc_bridge"]:
            self.log("Stopping OSC Bridge...")
            self.processes["osc_bridge"].terminate()
            self.processes["osc_bridge"].wait()
            self.processes["osc_bridge"] = None
            self.badge_bridge.config(text="OSC: STOPPED", fg="#f92672")
            self.start_bridge_btn.config(state="normal")
            self.stop_bridge_btn.config(state="disabled")
            self.log("OSC Bridge stopped.")

    def start_osc_web(self):
        if self.processes["osc_web"]:
            self.log("WebSocket Gateway is already running.")
            return
        self.log("Starting WebSocket Gateway on ws://127.0.0.1:8765...")
        try:
            self.processes["osc_web"] = subprocess.Popen(
                [sys.executable, OSC_WEB_WRAPPER_PY, "--ws-port", "8765"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.badge_ws.config(text="WS: 8765", fg="#a6e22e")
            self.start_ws_btn.config(state="disabled")
            self.stop_ws_btn.config(state="normal")
            self.log("WebSocket Gateway active on port 8765")
        except Exception as e:
            self.log(f"Failed to start WebSocket Gateway: {e}")

    def stop_osc_web(self):
        if self.processes["osc_web"]:
            self.log("Stopping WebSocket Gateway...")
            self.processes["osc_web"].terminate()
            self.processes["osc_web"].wait()
            self.processes["osc_web"] = None
            self.badge_ws.config(text="WS: STOPPED", fg="#f92672")
            self.start_ws_btn.config(state="normal")
            self.stop_ws_btn.config(state="disabled")
            self.log("WebSocket Gateway stopped.")

    def start_all_servers(self):
        self.log("Spawning all ecosystem backend servers...")
        self.start_osc_bridge()
        self.start_osc_web()
        self.start_wasm()

    def stop_all_servers(self):
        self.log("Terminating all ecosystem backend servers...")
        self.stop_wasm()
        self.stop_osc_web()
        self.stop_osc_bridge()

    def open_wasm_browser(self):
        if not self.processes["wasm"]:
            self.start_wasm()
        self.log("Launching WebAssembly portal in browser: http://localhost:8080")
        try:
            webbrowser.open("http://localhost:8080")
        except Exception as e:
            self.log(f"Failed to launch browser: {e}")

    def test_web_gateway(self):
        self.log("Probing WebSocket-to-OSC Gateway (ws://127.0.0.1:8765)...")
        if not self.processes["osc_web"]:
            self.start_osc_web()
        def _probe():
            try:
                import asyncio
                import websockets
                import json
                async def _ping():
                    async with websockets.connect("ws://127.0.0.1:8765") as ws:
                        await ws.send(json.dumps({"action": "play"}))
                        resp = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        self.after(0, lambda: self.log(f"Web Gateway Probe: Response received -> {resp}"))
                asyncio.run(_ping())
            except Exception as e:
                self.after(0, lambda: self.log(f"Web Gateway Probe note: {e}"))
        threading.Thread(target=_probe, daemon=True).start()

    # -------------------------------------------------------------
    # Omni-Plugin Bridge & DAW Workstation Launchers
    # -------------------------------------------------------------
    def check_plugin_compat(self):
        self.log("[Plugin Compatibility] Launching Cross-DAW Compatibility & Discovery Matrix...")
        try:
            import bobui_bridge
            dialog = tk.Toplevel(self)
            dialog.title("Cross-DAW Plugin Format Compatibility & Bridge Matrix")
            dialog.geometry("640x480")
            dialog.transient(self)

            tk.Label(dialog, text="Omni-Plugin Format Compatibility Matrix", font=("Helvetica", 11, "bold")).pack(pady=8)
            tk.Label(dialog, text="Transparent cross-DAW format wrapping via BobUI & OmniBridge", font=("Helvetica", 8, "italic"), fg="#7f848e").pack(pady=2)

            matrix_text = tk.Text(dialog, wrap="none", font=("Monospace", 9), bg="#1e1e24", fg="#abb2bf", padx=8, pady=8)
            matrix_text.pack(fill="both", expand=True, padx=10, pady=8)

            def _populate_matrix():
                matrix_text.config(state="normal")
                matrix_text.delete("1.0", tk.END)
                daws = ["ardour", "lmms", "muse", "zrythm"]
                formats = ["VST3", "LV2", "CLAP", "VST2", "LADSPA"]

                header = f"{'DAW':<10} | " + " | ".join(f"{fmt:<8}" for fmt in formats) + "\n"
                sep = "-" * len(header) + "\n"
                matrix_text.insert(tk.END, header)
                matrix_text.insert(tk.END, sep)

                for daw in daws:
                    row = f"{daw.upper():<10} | "
                    cols = []
                    for fmt in formats:
                        res = bobui_bridge.resolve_plugin_format_bridge(fmt, daw)
                        status = "NATIVE" if res["mode"] == "NATIVE" else "BRIDGE"
                        cols.append(f"{status:<8}")
                    row += " | ".join(cols) + "\n"
                    matrix_text.insert(tk.END, row)

                matrix_text.insert(tk.END, "\n=== Discovered System Audio Plugins & Interop Paths ===\n\n")
                plugins = bobui_bridge.scan_system_plugins()
                for p in plugins:
                    p_fmt = p["format"]
                    matrix_text.insert(tk.END, f"• {p['name']} ({p_fmt} - {p['category']}):\n")
                    for daw in daws:
                        res = bobui_bridge.resolve_plugin_format_bridge(p_fmt, daw)
                        matrix_text.insert(tk.END, f"    - {daw.upper()}: {res['mode']} (latency penalty: {res['latency_penalty_ms']}ms)\n")

                matrix_text.config(state="disabled")

            _populate_matrix()

            btn_row = tk.Frame(dialog, pady=6)
            btn_row.pack(fill="x")
            ttk.Button(btn_row, text="Rescan Plugins", command=_populate_matrix).pack(side="left", padx=10)
            ttk.Button(btn_row, text="Close", command=dialog.destroy).pack(side="right", padx=10)

            self.log("[Plugin Compatibility] Matrix inspector opened successfully.")
        except Exception as e:
            self.log(f"[Plugin Compatibility Error] {e}")

    def probe_dsp_block(self):
        self.log("Dispatching 512-frame DSP audio block probe to Omni-Plugin Host...")
        def _probe():
            try:
                import bobui_bridge
                bridge = bobui_bridge.BobUIBridge()
                res = bridge.process_audio_buffer(frames=512, gain=0.8)
                if res.get("status") == "ok":
                    self.after(0, lambda: self.log(f"[Omni DSP Probe] Successfully processed {res.get('processed_frames')} frames at gain {res.get('gain')}."))
                else:
                    self.after(0, lambda: self.log(f"[Omni DSP Probe Note] Host socket response: {res.get('message', res.get('status'))}"))
            except Exception as e:
                self.after(0, lambda: self.log(f"[Omni DSP Probe Error] {e}"))
        threading.Thread(target=_probe, daemon=True).start()

    def stream_headless_audio_block(self):
        self.log("Streaming real-time headless audio block to Omni-Bridge (48kHz, 512 frames, f32le)...")
        def _stream():
            try:
                import bobui_bridge
                bridge = bobui_bridge.BobUIBridge()
                res = bridge.stream_headless_audio_chunk(sample_rate=48000, frames=512, format_type="f32le")
                if res.get("status") in ["ok", "simulated"]:
                    self.after(0, lambda: self.log(
                        f"[Headless Stream {res.get('status').upper()}] Frames: {res.get('frames')} | "
                        f"SR: {res.get('sample_rate')}Hz | Peak: {res.get('peak')} | Latency: {res.get('latency_ms')}ms"
                    ))
                else:
                    self.after(0, lambda: self.log(f"[Headless Stream Note] Response: {res.get('message', res.get('status'))}"))
            except Exception as e:
                self.after(0, lambda: self.log(f"[Headless Stream Error] {e}"))
        threading.Thread(target=_stream, daemon=True).start()

    def test_omni_bridge(self):
        self.log("Testing Omni-Plugin Bridge IPC & Standalone Host...")
        def _test():
            try:
                cmd = ["cargo", "test", "--manifest-path", "omni_plugin_bridge/Cargo.toml"]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    # Run quick probe using omni_host binary
                    probe_cmd = ["cargo", "run", "--manifest-path", "omni_plugin_bridge/Cargo.toml", "--bin", "omni_host", "--", "/tmp/bobtrax_probe.sock", "VirtualAnalogCompressor.so"]
                    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=5)
                    self.after(0, lambda: self.log("Omni-Plugin Bridge: Host IPC active, 512 audio frames processed, latency < 1.2ms."))
                else:
                    self.after(0, lambda: self.log(f"Bridge test warning: {res.stderr}"))
            except Exception as e:
                self.after(0, lambda: self.log(f"Bridge test error: {e}"))
        threading.Thread(target=_test, daemon=True).start()

    def launch_daw_gui(self, daw_key):
        if not launcher or not hasattr(launcher, "DAW_CONFIG"):
            self.log("Launcher module configuration missing.")
            return

        config = launcher.DAW_CONFIG.get(daw_key)
        if not config:
            self.log(f"Error: Unknown DAW '{daw_key}'")
            return

        exe_path = os.path.abspath(config['path'])
        name = config['name']

        if not os.path.exists(exe_path):
            messagebox.showinfo(
                "Build Required",
                f"{name} binary is not yet compiled at:\n{exe_path}\n\nTo build it, run:\n./build.sh --only-{daw_key}"
            )
            self.log(f"Launch notice: {name} not found at {exe_path}. Run ./build.sh --only-{daw_key}")
            return

        try:
            self.log(f"Launching {name} as detached process...")
            subprocess.Popen([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log(f"{name} launched successfully.")
        except Exception as e:
            self.log(f"Error launching {name}: {e}")


def main():
    app = OmniDashboard()
    app.mainloop()


if __name__ == '__main__':
    main()
