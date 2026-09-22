"""Convenience script to run the demo data seeder from repository root."""

import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.scripts.seed_demo_data import seed_demo_data

if __name__ == "__main__":
    seed_demo_data()
