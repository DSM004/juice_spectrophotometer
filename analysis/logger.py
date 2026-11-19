"""
logger.py: save the Arduino's serial output to a CSV file on your laptop
==========================================================================
The Nano prints one CSV line per reading over USB (e.g. "F1,F2,...,NIR" values).
This script adds the laptop's time and a sample LABEL to each line and saves it in
data/raw/YYYY-MM-DD_HHMM_<test>.csv, the format that pipeline.py reads.

Run (from the repo's top folder; close the Arduino Serial Monitor first!):
    python analysis/logger.py T3_dye_series
While it runs:
    type a new label and press Enter to change it, e.g.   dark   blank   c25   c100
    type  q  and press Enter (or press Ctrl+C) to stop.
Labels the pipeline understands: dark, blank, c<number> (concentration in %).

Needs: pip install pyserial
Licence: MIT
"""

import csv
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import serial                      # from the pyserial package
from serial.tools import list_ports

BAUD = 115200                      # must match Serial.begin(...) in the Arduino sketch
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def find_port():
    """Pick the Nano's port automatically (a 'usbmodem' port on a Mac)."""
    ports = [p.device for p in list_ports.comports()]
    for p in ports:
        if "usbmodem" in p or "ACM" in p or "COM" in p:
            return p
    sys.exit(f"No Arduino port found. Ports seen: {ports}. Is it plugged in, "
             "and is the Serial Monitor closed?")


def main():
    test_name = sys.argv[1] if len(sys.argv) > 1 else "test"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / f"{datetime.now():%Y-%m-%d_%H%M}_{test_name}.csv"

    port = find_port()
    ser = serial.Serial(port, BAUD, timeout=1)
    time.sleep(2)                  # give the board a moment after opening the port
    ser.reset_input_buffer()

    state = {"label": "dark", "running": True}

    def read_keyboard():
        """Runs in the background: each line you type becomes the new label."""
        while state["running"]:
            try:
                text = input().strip()
            except EOFError:
                break
            if text.lower() == "q":
                state["running"] = False
            elif text:
                state["label"] = text
                print(f"  -> label is now '{text}'")

    threading.Thread(target=read_keyboard, daemon=True).start()

    print(f"Logging from {port} to {out_path}")
    print("Current label: 'dark'. Type a new label + Enter to change it; 'q' + Enter to stop.\n")

    header_written = False
    n_rows = 0
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        try:
            while state["running"]:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(",")]

                # The sketch's first line is a header (column names, not numbers)
                if not header_written and not parts[0].replace(".", "").replace("-", "").isdigit():
                    writer.writerow(["pc_time", "label"] + parts)
                    header_written = True
                    print("Header:", line)
                    continue
                if not header_written:      # no header from the sketch: make a generic one
                    writer.writerow(["pc_time", "label"] + [f"col{i}" for i in range(len(parts))])
                    header_written = True

                writer.writerow([datetime.now().isoformat(timespec="milliseconds"),
                                 state["label"]] + parts)
                f.flush()                   # save every line straight away
                n_rows += 1
                print(f"[{state['label']}] {line}")
        except KeyboardInterrupt:
            pass
        finally:
            state["running"] = False
            ser.close()
    print(f"\nStopped. {n_rows} rows saved to {out_path}")


if __name__ == "__main__":
    main()
