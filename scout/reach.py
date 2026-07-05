"""Diagnostic CLI for bundled agent-reach social media capabilities.

This script exposes the agent-reach CLI directly from ai-chaos-scout
so you can easily verify logins and capabilities without a global install.

Usage:
    python scout/reach.py doctor
    python scout/reach.py install
"""

import sys
import os

# Ensure the bundled agent-reach module can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ext"))

from agent_reach.cli import main

if __name__ == "__main__":
    sys.exit(main())
