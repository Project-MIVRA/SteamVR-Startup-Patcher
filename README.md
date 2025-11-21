# **SteamVR Startup Patcher**

A simple GUI utility to automatically launch external applications (overlays, drivers, tools) when SteamVR starts.

## **Features**

* **Auto-Launch:** Force any .exe or .bat to start alongside SteamVR.  
* **Generates Manifest:** Automatically generates the required .vrmanifest JSON.  
* **Kill Switch:** Includes a button to force-kill SteamVR if it becomes unresponsive.

## **Installation**

Download the latest Build in the releases tab.

## **Running/Building from source**



## **Usage**

1. Run the script: python steamvr\_startup\_patcher.py  
2. **Target Application:** Browse for the executable you want to auto-start.  
3. **App Type:** Check "Dashboard Overlay" for tools/widgets; uncheck for full games.  
4. Click **REGISTER & AUTO-LAUNCH**.  
5. **Restart SteamVR** to see changes.

## **Troubleshooting**

* **App registered but not starting?** Check SteamVR Settings \> *Startup / Shutdown* \> *Choose Startup Overlay Apps* and ensure the toggle is "On".  
* **Stuck?** Use the "Force Kill SteamVR" button to reset the VR runtime.
