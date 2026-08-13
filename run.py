"""Unified entry point for the AI/ML Quantitative Trading System.

Starts:
    1. FastAPI backend (uvicorn) on port 8000
    2. Opens browser to the frontend

Usage:
    python run.py
    python run.py --port 8000
    python run.py --no-browser
"""
import argparse
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="AI/ML Quantitative Trading System")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    parser.add_argument("--dev", action="store_true", help="Run in dev mode (with Vite dev server)")
    args = parser.parse_args()

    if getattr(sys, 'frozen', False):
        web_dir = Path(sys._MEIPASS) / "web"
    else:
        web_dir = Path(__file__).parent / "web"
        
    dist_dir = web_dir / "dist"

    if args.dev and web_dir.exists():
        # Start Vite dev server in background
        print("Starting Vite dev server on http://localhost:5173 ...")
        vite_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(web_dir),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        frontend_url = "http://localhost:5173"
    else:
        vite_proc = None
        frontend_url = f"http://{args.host}:{args.port}"

    if not args.no_browser:
        def open_browser():
            time.sleep(3)
            webbrowser.open(frontend_url)
        threading.Thread(target=open_browser, daemon=True).start()

    print(f"""
    ==============================================================
               AI/ML Quantitative Trading System v2.0            
                                                               
       API Server:   http://{args.host}:{args.port}                     
       Frontend:     {frontend_url:<45s}
       API Docs:     http://{args.host}:{args.port}/docs                
                                                               
       Press Ctrl+C to stop                                       
    ==============================================================
    """)

    try:
        if getattr(sys, 'frozen', False):
            from api_server import api
            uvicorn.run(
                api,
                host=args.host,
                port=args.port,
                log_level="info",
            )
        else:
            uvicorn.run(
                "api_server:api",
                host=args.host,
                port=args.port,
                reload=args.dev,
                log_level="info",
            )
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if vite_proc:
            vite_proc.terminate()


if __name__ == "__main__":
    main()
