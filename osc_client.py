import time
import os
import configparser
from pythonosc import udp_client

# ===========================================
# Configuration System (Reads/Writes config.ini)
# ===========================================

CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()

if not os.path.exists(CONFIG_FILE):
    config["Resolume"] = {
        "ip": "127.0.0.1",
        "port": "7000"
    }
    config["MagicQ"] = {
        "ip": "192.168.0.100",
        "port": "8000"
    }
    with open(CONFIG_FILE, "w") as f:
        config.write(f)
    print(f"[Setup] Created default {CONFIG_FILE} file. You can edit it later to change IPs and ports.")

config.read(CONFIG_FILE)

RESOLUME_IP = config.get("Resolume", "ip", fallback="127.0.0.1")
RESOLUME_PORT = config.getint("Resolume", "port", fallback=7000)
MAGICQ_IP = config.get("MagicQ", "ip", fallback="192.168.0.100")
MAGICQ_PORT = config.getint("MagicQ", "port", fallback=8000)

# ===========================================
# OSC Clients
# ===========================================
resolume_client = udp_client.SimpleUDPClient(RESOLUME_IP, RESOLUME_PORT)
magicq_client = udp_client.SimpleUDPClient(MAGICQ_IP, MAGICQ_PORT)

# ===========================================
# State Tracking
# ===========================================
last_bpm_sent_resolume = None
last_bpm_sent_magicq = None

# ===========================================
# Helper Functions
# ===========================================

def scale_bpm(bpm, min_bpm, max_bpm):
    """Ensure BPM stays within given range and scale if necessary."""
    if bpm < min_bpm:
        bpm = min_bpm
    elif bpm > max_bpm:
        bpm = max_bpm
    return bpm


def send_bpm_to_resolume(bpm):
    global last_bpm_sent_resolume
    if bpm != last_bpm_sent_resolume:
        scaled_bpm = scale_bpm(bpm, 20, 500)
        try:
            # Updated OSC address for Resolume
            resolume_client.send_message("/composition/tempocontroller/tempo", scaled_bpm)
            print(f"[Resolume] Sent BPM: {scaled_bpm} → {RESOLUME_IP}:{RESOLUME_PORT}")
            last_bpm_sent_resolume = bpm
        except Exception as e:
            print(f"[Resolume] Error sending BPM: {e}")


def send_bpm_to_magicq(bpm):
    global last_bpm_sent_magicq
    if bpm != last_bpm_sent_magicq:
        scaled_bpm = scale_bpm(bpm, 0, 500)
        try:
            magicq_client.send_message("/bpm", scaled_bpm)
            print(f"[MagicQ] Sent BPM: {scaled_bpm} → {MAGICQ_IP}:{MAGICQ_PORT}")
            last_bpm_sent_magicq = bpm
        except Exception as e:
            print(f"[MagicQ] Error sending BPM: {e}")


def send_bpm_to_all(bpm):
    """Send BPM to both Resolume and MagicQ with proper scaling."""
    send_bpm_to_resolume(bpm)
    send_bpm_to_magicq(bpm)


# ===========================================
# Example Usage (for testing)
# ===========================================
if __name__ == "__main__":
    print("OSC Client for BPM-to-OSC initialized with config file support.")
    print(f"Resolume  → {RESOLUME_IP}:{RESOLUME_PORT}")
    print(f"MagicQ    → {MAGICQ_IP}:{MAGICQ_PORT}")
    print("Sending test BPM values... (press Ctrl+C to stop)")
    try:
        bpm_test_values = [120, 121, 121, 122, 125, 125, 128]
        for bpm in bpm_test_values:
            send_bpm_to_all(bpm)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user.")
