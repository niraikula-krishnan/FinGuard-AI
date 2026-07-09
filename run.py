#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def main():
    print("=" * 60)
    print("           FinGuard-AI One-Click App Runner             ")
    print("=" * 60)
    
    # 1. Determine platform and paths
    is_windows = platform.system() == "Windows"
    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
    
    if is_windows:
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        uvicorn_exe = os.path.join(venv_dir, "Scripts", "uvicorn.exe")
    else:
        python_exe = os.path.join(venv_dir, "bin", "python")
        pip_exe = os.path.join(venv_dir, "bin", "pip")
        uvicorn_exe = os.path.join(venv_dir, "bin", "uvicorn")
        
    # 2. Create virtual environment if missing
    if not os.path.exists(venv_dir):
        print(f"Creating Python Virtual Environment in {venv_dir}...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}", file=sys.stderr)
            sys.exit(1)
            
    # 3. Upgrade pip and install requirements
    print("Installing python dependencies...")
    requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    try:
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_exe, "install", "-r", requirements_path], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}", file=sys.stderr)
        sys.exit(1)
        
    # 4. Start the FastAPI App
    print("\n" + "-" * 50)
    print("Launching FinGuard-AI Server...")
    print("Open your browser and visit: http://localhost:8080")
    print("-" * 50 + "\n")
    
    # Run Uvicorn on Port 8080 to prevent conflicts
    app_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess.run([uvicorn_exe, "main:app", "--reload", "--port", "8080"], cwd=app_dir)
    except KeyboardInterrupt:
        print("\nFinGuard-AI Server stopped.")
    except Exception as e:
        print(f"Error running server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
