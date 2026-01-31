import streamlit as st
import json
import pandas as pd
from datetime import datetime
import re

st.title("GPS, SDM & System Activity Visualizer")

uploaded_files = st.file_uploader(
    "Upload up to 3 log files", type=["log", "txt"], accept_multiple_files=True
)

if uploaded_files:
    all_gps_points = []
    summary_data = []
    wifi_data = []
    sdm_data = []
    wan_data = []
    telemetry_data = []
    call_data = []

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
