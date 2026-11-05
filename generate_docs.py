#!/usr/bin/env python3
"""
Bobtrax Documentation Governance & Verification Utility

Audits, validates, and synchronizes project documentation files
without destructively overwriting established project state.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))

REQUIRED_DOCS = [
    "VERSION.md",
    "CHANGELOG.md",
    "README.md",
    "VISION.md",
    "ROADMAP.md",
    "TODO.md",
    "DEPLOY.md",
    "MEMORY.md",
    "HANDOFF.md",
    "Manual.md",
    "PROJECT_STRUCTURE.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "GPT.md",
    "copilot-instructions.md"
]

def audit_docs():
    print("=== Bobtrax Documentation Audit ===")
    missing = []
    for doc in REQUIRED_DOCS:
        path = os.path.join(REPO_ROOT, doc)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✓ {doc:<24} ({size} bytes)")
        else:
            print(f"✗ {doc:<24} MISSING")
            missing.append(doc)

    # Check version alignment
    v_path = os.path.join(REPO_ROOT, "VERSION.md")
    if os.path.exists(v_path):
        with open(v_path) as vf:
            ver = vf.read().strip()
            print(f"\nCurrent Recorded Version: v{ver}")

    if missing:
        print(f"\nWarning: Missing {len(missing)} required documentation files.")
        return False

    print("\nAll required documentation files are present and tracked.")
    return True

if __name__ == "__main__":
    success = audit_docs()
    sys.exit(0 if success else 1)
