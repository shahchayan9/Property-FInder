#!/usr/bin/env python3
"""
Run the Property Finder ASI1 agent.
Usage (from this directory):
  python run_agent.py
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent  # Property-FInder/
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

if __name__ == "__main__":
    from asi1_agent.property_agent import agent
    print("Property Finder agent address:", agent.address)
    agent.run()
