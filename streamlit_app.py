import streamlit as st
import json
import pandas as pd
from datetime import datetime
import re
import altair as alt

st.title("GPS, SDM & System Activity Visualizer")

# --- Ініціалізація змінних тут, щоб уникнути NameError ---
all_gps_points = []
summary_data = []
wifi_data = []
sdm_data = []
wan_data = []
telemetry_data = []
call_data = []

uploaded_files = st.file_uploader(
    "Upload up to 3 log files", type=["log", "txt"], accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            log_text = uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception as e:
            st.error(f"Failed to read file {uploaded_file.name}: {e}")
            continue

        gps_points = []
        last_gps_time = None

        for line in log_text.splitlines():
            # --- GPS & WiFi RSSI ---
            if '{"status"' in line:
                try:
                    json_part = line[line.index("{"):]
                    j = json.loads(json_part)

                    gps = j.get("gps", {})
                    if gps.get("fix") and "latitude" in gps and "longitude" in gps:
                        gps_points.append({
                            "lat": gps["latitude"],
                            "lon": gps["longitude"],
                            "file": uploaded_file.name
                        })

                    # WiFi RSSI
                    wlan = j.get("wlanAsClientStatus", {})
                    rssi = wlan.get("rssi")
                    utc_time = gps.get("utc")
                    date = gps.get("date")
                    if rssi is not None and utc_time and date:
                        try:
                            dt_str = f"{date} {utc_time}"
                            dt = datetime.strptime(dt_str, "%d%m%y %H%M%S.%f")
                            last_gps_time = dt
                        except Exception:
                            dt = last_gps_time
                        wifi_data.append({
                            "time": dt,
                            "rssi": rssi,
                            "file": uploaded_file.name
                        })

                    # WAN connectivity
                    wan_in_use = j.get("status", {}).get("wanInUse")
                    if dt:
                        wan_data.append({
                            "time": dt,
                            "wan": wan_in_use,
                            "file": uploaded_file.name
                        })
                except Exception:
                    continue

            # --- SDM Data ---
            if "SDM Data:" in line:
                match = re.search(r"SDM Data: (>>|<<)\s*(.*)", line)
                if match:
                    direction = match.group(1)  # >> або <<
                    hex_bytes = match.group(2).split()
                    byte_count = len(hex_bytes)
                    timestamp = last_gps_time if last_gps_time else None
                    sdm_data.append({
                        "time": timestamp,
                        "bytes": byte_count,
                        "direction": "TX" if direction == ">>" else "RX",
                        "file": uploaded_file.name
                    })

            # --- Telemetry send success/failure ---
            if "SendRegHeartbeat" in line or "handleRegHeartbeatResp" in line:
                timestamp = last_gps_time
                success = "SUCCESS" in line
                telemetry_data.append({
                    "time": timestamp,
                    "success": int(success),
                    "file": uploaded_file.name
                })

            # --- Call / Talkgroup activity ---
            if "ProcessEvent event ev_sdm_" in line or "Received PMSG from Call Management" in line:
                timestamp = last_gps_time
                call_data.append({
                    "time": timestamp,
                    "event": line.strip(),
                    "file": uploaded_file.name
                })

        all_gps_points.extend(gps_points)
        summary_data.append({
            "file": uploaded_file.name,
            "gps_points": len(gps_points)
        })
