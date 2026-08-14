import os
import subprocess
import sys

def build():
    print("Building frontend...")
    # Run npm build
    try:
        subprocess.run(["npm", "run", "build"], cwd="web", check=True, shell=True)
    except subprocess.CalledProcessError:
        print("Failed to build frontend. Please ensure Node.js is installed.")
        sys.exit(1)

    print("Installing PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    print("Building executable...")
    # Add web/dist to the package
    sep = ";" if os.name == "nt" else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "QuantumGrow",
        "--add-data", f"web/dist{sep}web/dist",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "sqlite3",
        "--hidden-import", "numpy",
        "--hidden-import", "pandas",
        "--hidden-import", "scikit-learn",
        "--onefile",
        "run.py"
    ]
    
    subprocess.run(cmd, check=True)
    
    print("\n[SUCCESS] Build complete!")
    print("Your executable is located in the 'dist' folder.")
    print("Executable name: dist/QuantumGrow.exe")

if __name__ == "__main__":
    build()
