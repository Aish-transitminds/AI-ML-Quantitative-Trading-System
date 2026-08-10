"""PyInstaller build script for the AI/ML Stock Screener.

Creates a Windows executable launcher that starts the Streamlit dashboard.

Usage:
    python build_exe.py

The generated EXE will:
    1. Launch 'streamlit run app.py' as a subprocess
    2. Open the default browser to http://localhost:8501
    3. Wait for the user to close the terminal
"""
import subprocess
import sys
from pathlib import Path


def create_launcher():
    """Create the launcher script that PyInstaller will package."""
    launcher_code = '''
"""Stock Screener Launcher — Opens the Streamlit dashboard."""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path


def main():
    print("=" * 60)
    print("  AI/ML Stock Market Screening and Analysis System")
    print("=" * 60)
    print()
    print("Starting dashboard server...")
    print("The dashboard will open in your browser automatically.")
    print("Press Ctrl+C to stop the server.")
    print()

    # Determine paths
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent

    app_path = base_dir / "app.py"

    if not app_path.exists():
        print(f"ERROR: app.py not found at {app_path}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Launch Streamlit
    port = os.environ.get("DASHBOARD_PORT", "8501")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", port,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]

    try:
        proc = subprocess.Popen(cmd)

        # Wait a moment then open browser
        time.sleep(3)
        url = f"http://localhost:{port}"
        print(f"Opening browser: {url}")
        webbrowser.open(url)

        # Wait for process
        proc.wait()

    except KeyboardInterrupt:
        print("\\nShutting down...")
        proc.terminate()
        proc.wait(timeout=5)
        print("Server stopped.")

    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
'''

    launcher_path = Path("launcher.py")
    launcher_path.write_text(launcher_code.strip())
    return launcher_path


def build():
    """Build the Windows executable."""
    print("Building Windows executable...")
    print()

    # Create launcher
    launcher_path = create_launcher()

    # Collect data files
    data_files = [
        ("app.py", "."),
        ("config", "config"),
        ("broker", "broker"),
        ("data", "data"),
        ("indicators", "indicators"),
        ("features", "features"),
        ("signals", "signals"),
        ("ml", "ml"),
        ("dashboard", "dashboard"),
        ("storage", "storage"),
        ("utils", "utils"),
        ("demo", "demo"),
    ]

    add_data_args = []
    for src, dst in data_files:
        if Path(src).exists():
            add_data_args.extend(["--add-data", f"{src};{dst}"])

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "StockScreener",
        "--onedir",  # Folder distribution (faster startup)
        "--console",  # Show console for logs
        "--noconfirm",
        "--clean",
        *add_data_args,
        str(launcher_path),
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print()
        print("=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Executable: dist/StockScreener/StockScreener.exe")
        print("=" * 60)
    else:
        print()
        print("BUILD FAILED!")
        sys.exit(1)

    # Clean up
    launcher_path.unlink(missing_ok=True)


if __name__ == "__main__":
    build()
