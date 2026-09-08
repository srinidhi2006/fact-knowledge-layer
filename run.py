"""
Unified Runner for Fact Knowledge Layer.
Usage:
    python run.py backend      # Start FastAPI backend (http://127.0.0.1:8000)
    python run.py frontend     # Start Streamlit UI (http://localhost:8501)
    python run.py ingest       # Ingest Delhivery starter dataset
    python run.py evaluate     # Execute benchmark test cases
"""

import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "backend":
        print("Starting FastAPI Backend at http://127.0.0.1:8000...")
        subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"])

    elif command == "frontend":
        print("Starting Streamlit Frontend at http://localhost:8501...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py"])

    elif command == "ingest":
        dataset = sys.argv[2] if len(sys.argv) > 2 else "delhivery"
        subprocess.run([sys.executable, "scripts/ingest_dataset.py", "--dataset", dataset])

    elif command == "evaluate":
        subprocess.run([sys.executable, "scripts/evaluate_demo_cases.py"])

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
