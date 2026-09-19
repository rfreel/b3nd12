#!/usr/bin/env python3
"""Repository-local agent interface. Run with --help for commands."""
import sys

sys.dont_write_bytecode = True

from tools.agent_system.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
