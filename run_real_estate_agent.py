#!/usr/bin/env python3
"""
Run the Real Estate Report Agent (deep research backend).

This agent pairs with the Property-FInder agent. It receives ReportRequest
messages from Property-FInder, fetches all Repliers listings, creates a
Google Sheet, emails the sheet URL, and replies with ReportResponse.

Usage (from this directory):
    python run_real_estate_agent.py

Both agents can run simultaneously — they communicate via ctx.send() on Agentverse.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

if __name__ == "__main__":
    from real_estate_agent.agent import agent
    print("Real Estate Report Agent address:", agent.address)
    print("Copy this address into REAL_ESTATE_AGENT_ADDRESS in asi1_agent/.env")
    agent.run()
