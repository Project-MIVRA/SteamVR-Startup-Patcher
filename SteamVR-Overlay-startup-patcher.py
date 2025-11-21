import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import json
import os
import threading
import subprocess
import time

# Try to import openvr
try:
    import openvr
except ImportError:
    openvr = None

class OpenVRManager:
    """
    Context Manager to ensure OpenVR shuts down cleanly 
    even if errors occur within the block.
    """
    def __init__(self, app_type=None):
        self.app_type = app_type if app_type else openvr.VRApplication_Utility
        self.system = None

    def __enter__(self):
        try:
            self.system = openvr.init(self.app_type)
            return openvr.VRApplications()
        except openvr.VRApplicationError as e:
            raise e

    def __exit__(self, exc_type, exc_value, traceback):
        if self.system:
            openvr.shutdown()
            self.system = None

class SteamVRStartupPatcher:
    def __init__(self, root):
        self.root = root
        self.root.title("SteamVR Startup Patcher")
        self.root.geometry("650x550")
        
        # Variables
        self.app_path = tk.StringVar()
        self.app_name = tk.StringVar()
        self.is_overlay = tk.BooleanVar(value=True) # Default to Overlay (Dashboard tool)
        
        self.check_dependencies()
        self.create_widgets()

    def check_dependencies(self):
        if openvr is None:
            messagebox.showerror("Dependency Error", "The 'openvr' library is missing.\nPlease run: pip install openvr")
            self.root.destroy()

    def create_widgets(self):
        # --- Header ---
        tk.Label(self.root, text="SteamVR Startup Patcher", font=("Segoe UI", 16, "bold")).pack(pady=10)
        tk.Label(self.root, text="Auto-launch external apps when VR starts", fg="gray").pack(pady=(0, 10))
        
        # --- Section 1: Target Application ---
        lbl_frame_app = tk.LabelFrame(self.root, text="Target Application", padx=10, pady=10)
        lbl_frame_app.pack(fill="x", padx=10, pady=5)

        # Path Selection
        tk.Label(lbl_frame_app, text="Executable (.exe/.bat):").pack(anchor="w")
        frame_app_select = tk.Frame(lbl_frame_app)
        frame_app_select.pack(fill="x", pady=(0, 10))
        
        tk.Entry(frame_app_select, textvariable=self.app_path).pack(side="left", fill="x", expand=True)
        tk.Button(frame_app_select, text="Browse", command=self.browse_app).pack(side="right", padx=5)

        # Name and Type
        frame_details = tk.Frame(lbl_frame_app)
        frame_details.pack(fill="x")
        
        # Name Input
        frame_name = tk.Frame(frame_details)
        frame_name.pack(side="left", fill="x", expand=True)
        tk.Label(frame_name, text="Display Name:").pack(anchor="w")
        tk.Entry(frame_name, textvariable=self.app_name).pack(fill="x", padx=(0, 5))

        # App Type Checkbox
        frame_type = tk.Frame(frame_details)
        frame_type.pack(side="right")
        tk.Label(frame_type, text="App Type:").pack(anchor="w")
        tk.Checkbutton(frame_type, text="Dashboard Overlay", variable=self.is_overlay).pack(anchor="w")
        
        # --- Section 2: Action ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.btn_action = tk.Button(btn_frame, text="REGISTER & AUTO-LAUNCH", bg="#4CAF50", fg="white", 
                               font=("Segoe UI", 10, "bold"), command=self.start_patch_thread, height=2)
        self.btn_action.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_kill = tk.Button(btn_frame, text="FORCE KILL STEAMVR", bg="#d32f2f", fg="white",
                             font=("Segoe UI", 8), command=self.force_kill_steamvr, height=2)
        btn_kill.pack(side="right", padx=(5, 0))

        # --- Section 3: Console Log ---
        tk.Label(self.root, text="Process Log:", anchor="w").pack(fill="x", padx=10)
        self.log_text = scrolledtext.ScrolledText(self.root, height=10, state='disabled', font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def log(self, message, tag=None):
        """Thread-safe logging to the text widget"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f">> {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def browse_app(self):
        filename = filedialog.askopenfilename(filetypes=[("Executables", "*.exe *.bat *.cmd"), ("All files", "*.*")])
        if filename:
            # Normalize path separators
            filename = os.path.normpath(filename)
            self.app_path.set(filename)
            if not self.app_name.get():
                base = os.path.basename(filename)
                name = os.path.splitext(base)[0]
                self.app_name.set(name.title())

    def start_patch_thread(self):
        """Wrapper to run the patcher in a separate thread so UI doesn't freeze"""
        if not self.app_path.get():
            messagebox.showwarning("Missing Data", "Please select an executable.")
            return

        self.btn_action.config(state="disabled", text="Processing...")
        self.log("Starting patching process...", "info")
        
        t = threading.Thread(target=self.patch_logic)
        t.daemon = True
        t.start()

    def patch_logic(self):
        try:
            target_exe = self.app_path.get()
            display_name = self.app_name.get()
            
            # 1. Prepare Paths
            app_dir = os.path.dirname(target_exe)
            clean_key = "".join(x for x in display_name if x.isalnum()).lower()
            if not clean_key: clean_key = "unnamed_app"
            
            app_key = f"user.generated.{clean_key}"
            manifest_path = os.path.join(app_dir, f"{clean_key}.vrmanifest")

            self.log(f"Target: {target_exe}")
            self.log(f"Key: {app_key}")

            # 2. Create JSON Manifest
            # Important: Use forward slashes for JSON paths to avoid escape character issues
            json_binary_path = target_exe.replace(os.sep, "/")
            
            manifest_content = {
                "source": "builtin",
                "applications": [{
                    "app_key": app_key,
                    "launch_type": "binary",
                    "binary_path_windows": json_binary_path,
                    "is_dashboard_overlay": self.is_overlay.get(),
                    "name": display_name,
                    "strings": {"en_us": {"name": display_name}}
                }]
            }

            try:
                with open(manifest_path, "w") as f:
                    json.dump(manifest_content, f, indent=4)
                self.log(f"Manifest created at: {manifest_path}")
            except Exception as e:
                self.log(f"File Error: {e}")
                return

            # 3. Interact with OpenVR API
            self.log("Initializing OpenVR Runtime...")
            
            # Using the Context Manager to guarantee shutdown
            with OpenVRManager(openvr.VRApplication_Utility) as vr_apps:
                
                # A. Register Manifest
                self.log("Registering manifest...")
                error = vr_apps.addApplicationManifest(manifest_path, False)
                
                if error != openvr.VRApplicationError_None:
                    err_name = vr_apps.getApplicationsErrorNameFromEnum(error)
                    self.log(f"API Error (AddManifest): {err_name}")
                    return

                # Check if registration actually took hold
                if not vr_apps.isApplicationInstalled(app_key):
                    self.log("Warning: App Key not found immediately. Waiting...")
                    time.sleep(1.0)

                # B. Set Auto-Launch
                self.log("Enabling Auto-Launch...")
                error = vr_apps.setApplicationAutoLaunch(app_key, True)
                
                if error != openvr.VRApplicationError_None:
                    err_name = vr_apps.getApplicationsErrorNameFromEnum(error)
                    self.log(f"API Error (SetAutoLaunch): {err_name}")
                else:
                    self.log("SUCCESS: Application registered and auto-launch enabled!")
                    self.log("NOTE: Restart SteamVR for changes to take effect.")

        except openvr.VRApplicationError as e:
            self.log(f"OpenVR Initialization Failed. Is SteamVR installed? Error: {e}")
        except Exception as e:
            self.log(f"Unexpected Error: {e}")
        finally:
            # Re-enable UI
            self.root.after(0, lambda: self.btn_action.config(state="normal", text="REGISTER & AUTO-LAUNCH"))

    def force_kill_steamvr(self):
        if messagebox.askyesno("Force Kill", "Terminate vrserver.exe and vrcompositor.exe?\nUse only if SteamVR is stuck."):
            try:
                subprocess.run(["taskkill", "/F", "/IM", "vrserver.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["taskkill", "/F", "/IM", "vrcompositor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["taskkill", "/F", "/IM", "vrmonitor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.log("Sent kill commands to SteamVR processes.")
            except Exception as e:
                self.log(f"Failed to kill processes: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    # Set high DPI awareness for Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = SteamVRStartupPatcher(root)
    root.mainloop()