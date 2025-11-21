import subprocess
import sys
import os
import importlib.metadata

def install(package):
    print(f"--- Installing {package} ---")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_and_install_requirements():
    # 'openvr' is the package name for the python bindings
    required = {'pyinstaller', 'openvr'}
    
    installed = {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}
    
    for req in required:
        if req not in installed:
            print(f"Package '{req}' is missing. Installing...")
            install(req)
        else:
            print(f"Package '{req}' is installed.")

def build_executable():
    script_name = "SteamVR-Overlay-startup-patcher.py"
    output_name = "SteamVR_Startup_Patcher"

    if not os.path.exists(script_name):
        print(f"ERROR: Could not find {script_name}")
        print("Make sure this build script is in the same folder as your patcher script.")
        input("Press Enter to exit...")
        return

    print("--- Starting Build Process ---")
    print("This may take a minute...")

    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--uac-admin",
        # CRITICAL FIX: Force PyInstaller to grab the OpenVR DLLs and data
        "--collect-all=openvr",
        f"--name={output_name}",
        "--clean",
        script_name
    ]

    try:
        subprocess.check_call(args)
        print("\n" + "="*30)
        print("BUILD SUCCESSFUL!")
        print("="*30)
        print(f"Your .exe is located in the 'dist' folder: dist/{output_name}.exe")
    except subprocess.CalledProcessError as e:
        print(f"\nError during build: {e}")

if __name__ == "__main__":
    check_and_install_requirements()
    build_executable()
    input("\nPress Enter to close...")