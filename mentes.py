import json
import os
import time
import serial
import threading
import tkinter as tk
import platform
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("application.log"),
        logging.StreamHandler()
    ]
)

# Set fullscreen to True to activate fullscreen mode
fullscreen = False

class SimpleSerialApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Simple Serial App")

        # Configure fullscreen based on the operating system
        current_os = platform.system()
        if current_os == 'Windows':
            try:
                self.master.state('zoomed')  # Windows
                logging.info("Entered fullscreen mode on Windows.")
            except Exception as e:
                logging.error(f"Error setting fullscreen on Windows: {e}")
        elif current_os in ['Linux', 'Darwin']:
            try:
                self.master.attributes('-fullscreen', fullscreen)  # Unix/Linux/Mac
                logging.info(f"Entered fullscreen mode on {current_os}.")
            except Exception as e:
                # If '-fullscreen' doesn't work, manually set window size
                screen_width = self.master.winfo_screenwidth()
                screen_height = self.master.winfo_screenheight()
                self.master.geometry(f"{screen_width}x{screen_height}+0+0")
                logging.warning(f"Could not set fullscreen attribute on {current_os}: {e}")
                logging.info(f"Set window size to {screen_width}x{screen_height}.")

        # Exit fullscreen mode with the Escape key
        self.master.bind("<Escape>", self.exit_fullscreen)

        # Initialize serial port
        self.ser = None
        self.initialize_serial_port('/dev/cino')  # Update this path as needed

        # Initialize JSON data structures
        self.ksk_pmod = {}
        self.pmod_settings = {}
        self.ksk_pmod_path = 'ksk_pmod.json'
        self.pmod_settings_path = 'pmod_settings.json'

        # Track last modification times
        self.ksk_pmod_mtime = None
        self.pmod_settings_mtime = None

        # Lock for thread-safe access to JSON data
        self.json_lock = threading.Lock()

        # Load initial JSON data
        self.load_json_data()

        # Create GUI components
        self.create_widgets()

        # Start scanner thread
        self.scanner_device = '/dev/scan'  # Update this path as needed
        if os.path.exists(self.scanner_device):
            threading.Thread(target=self.read_from_scanner, args=(self.scanner_device,), daemon=True).start()
            logging.info(f"Monitoring scanner device: {self.scanner_device}")
        else:
            logging.error(f"Scanner device not found: {self.scanner_device}")

        # Start JSON watcher thread
        threading.Thread(target=self.watch_json_files, daemon=True).start()
        logging.info("Started JSON watcher thread.")

    def initialize_serial_port(self, port):
        """Initialize the serial port."""
        try:
            self.ser = serial.Serial(port, 9600, timeout=1)
            logging.info(f"Serial port '{port}' successfully opened.")
        except serial.SerialException as e:
            logging.error(f"Serial Port Error: Could not open serial port '{port}': {e}")
            self.ser = None

    def load_json_data(self):
        """Load ksk_pmod.json and pmod_settings.json."""
        with self.json_lock:
            # Load ksk_pmod.json
            try:
                current_mtime = os.path.getmtime(self.ksk_pmod_path)
                if self.ksk_pmod_mtime != current_mtime:
                    with open(self.ksk_pmod_path, 'r', encoding='utf-8') as f:
                        self.ksk_pmod = json.load(f)
                    self.ksk_pmod_mtime = current_mtime
                    logging.info(f"Loaded '{self.ksk_pmod_path}' successfully.")
            except FileNotFoundError:
                logging.error(f"File '{self.ksk_pmod_path}' not found.")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error in '{self.ksk_pmod_path}': {e}")
            except Exception as e:
                logging.error(f"Unexpected error loading '{self.ksk_pmod_path}': {e}")

            # Load pmod_settings.json
            try:
                current_mtime = os.path.getmtime(self.pmod_settings_path)
                if self.pmod_settings_mtime != current_mtime:
                    with open(self.pmod_settings_path, 'r', encoding='utf-8') as f:
                        self.pmod_settings = json.load(f)
                    self.pmod_settings_mtime = current_mtime
                    logging.info(f"Loaded '{self.pmod_settings_path}' successfully.")
            except FileNotFoundError:
                logging.error(f"File '{self.pmod_settings_path}' not found.")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error in '{self.pmod_settings_path}': {e}")
            except Exception as e:
                logging.error(f"Unexpected error loading '{self.pmod_settings_path}': {e}")

    def watch_json_files(self):
        """Continuously watch JSON files for changes and reload them."""
        logging.info("JSON watcher thread started.")
        while True:
            try:
                self.load_json_data()
            except Exception as e:
                logging.error(f"Error watching JSON files: {e}")
            time.sleep(1)  # Check every second

    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode with the Escape key."""
        current_os = platform.system()
        try:
            if current_os == 'Windows':
                self.master.state('normal')  # Windows
                logging.info("Exited fullscreen mode on Windows.")
            elif current_os in ['Linux', 'Darwin']:
                self.master.attributes('-fullscreen', False)  # Unix/Linux/Mac
                logging.info(f"Exited fullscreen mode on {current_os}.")
        except Exception as e:
            logging.error(f"Error exiting fullscreen mode on {current_os}: {e}")

    def create_widgets(self):
        """Create and layout GUI components."""
        self.master.configure(bg='white')  # Set background color
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        main_frame = tk.Frame(self.master, bg='white')
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Scanned Data Label centered
        scanned_frame = tk.Frame(main_frame, bg='white')
        scanned_frame.grid(row=0, column=0, pady=20, padx=20, sticky="nsew")
        scanned_frame.grid_rowconfigure(0, weight=1)
        scanned_frame.grid_columnconfigure(0, weight=1)

        self.scanned_var = tk.StringVar(value="HV")
        scanned_label = tk.Label(
            scanned_frame,
            textvariable=self.scanned_var,
            font=("Arial", 100, "bold"),
            fg='black',
            bg='white',
            anchor='center'
        )
        scanned_label.pack(expand=True)

        # Steps Label centered
        steps_frame = tk.Frame(main_frame, bg='white')
        steps_frame.grid(row=1, column=0, pady=20, padx=20, sticky="nsew")
        steps_frame.grid_rowconfigure(0, weight=1)
        steps_frame.grid_columnconfigure(0, weight=1)

        self.steps_var = tk.StringVar(value="")
        steps_label = tk.Label(
            steps_frame,
            textvariable=self.steps_var,
            font=("Arial", 80, "bold"),
            fg='black',
            bg='white',
            anchor='center'
        )
        steps_label.pack(expand=True)

    def update_scanned_data(self, data):
        """Safely update the 'Scanned Data' label."""
        self.scanned_var.set(data)
        logging.info(f"Scanned KSKNr updated: {data}")

    def update_steps(self, steps):
        """Safely update the 'Steps' label."""
        self.steps_var.set(str(steps))
        logging.info(f"Steps updated: {steps}")

    def find_and_send_steps(self, ksk_number):
        """
        Find the PMOD for the given KSK number and send the corresponding steps to the machine.
        """
        ksk_str = str(ksk_number)
        with self.json_lock:
            pmod_entry = self.ksk_pmod.get(ksk_str)

        if not pmod_entry:
            logging.warning(f"No PMOD found for KSKNr: {ksk_str}")
            self.update_steps("")
            return

        pmod_val = pmod_entry.get("pmod")
        if not pmod_val:
            logging.warning(f"No PMOD value found for KSKNr: {ksk_str}")
            self.update_steps("")
            return

        with self.json_lock:
            steps_entry = self.pmod_settings.get(pmod_val)

        if not steps_entry:
            logging.warning(f"No steps setting found for PMOD: {pmod_val}")
            self.update_steps("")
            return

        steps = steps_entry.get("steps", 1)  # Default to 1 if not specified

        logging.info(f"PMOD for KSKNr {ksk_str}: {pmod_val}")
        logging.info(f"Steps for PMOD {pmod_val}: {steps}")

        # Prepare the JSON command
        to_send = json.dumps({"V": "2", "S": str(steps)})

        try:
            if self.ser and self.ser.is_open:
                self.ser.write(to_send.encode('utf-8'))
                logging.info(f"Sent to machine: {to_send}")
                time.sleep(0.1)  # Brief pause to allow for device response
                response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    logging.info(f"Serial response: {response}")
                else:
                    logging.warning("No response from serial device.")
            else:
                logging.error("Serial port is not open.")
        except Exception as e:
            logging.error(f"Serial communication error: {e}")

        # Update the 'Steps' label
        self.update_steps(steps)

    def read_from_scanner(self, scanner_device):
        """Continuously read from the scanner device and process KSK numbers."""
        try:
            with open(scanner_device, 'rb') as scanner:
                logging.info(f"Started reading from scanner device: {scanner_device}")
                while True:
                    raw_line = scanner.readline()
                    if raw_line:
                        try:
                            decoded_line = raw_line.decode('latin-1', errors='ignore').strip()
                            digits = ''.join(ch for ch in decoded_line if ch.isdigit())
                            if digits:
                                logging.info(f"Scanned raw input: {decoded_line}")
                                logging.info(f"Extracted KSKNr: {digits}")
                                self.update_scanned_data(digits)
                                self.find_and_send_steps(int(digits))
                        except Exception as decode_error:
                            logging.error(f"Decoding error: {decode_error}")
                    else:
                        time.sleep(0.1)  # Avoid busy waiting
        except Exception as e:
            logging.error(f"Error reading from scanner: {e}")

def main():
    root = tk.Tk()
    app = SimpleSerialApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
