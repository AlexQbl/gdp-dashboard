import streamlit as st
import json
import pandas as pd
from datetime import datetime
import re

st.title("LOGS Visualizer")

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
                    direction = match.group(1)
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

    # --- Вивід GPS ---
    if all_gps_points:
        st.subheader("Map of all GPS points:")
        df_gps = pd.DataFrame(all_gps_points)
        st.map(df_gps[["lat", "lon"]])
    else:
        st.warning("No GPS points found in the uploaded files.")

    # --- Вивід WiFi RSSI ---
    if wifi_data:
        st.subheader("WiFi RSSI over time")
        df_wifi = pd.DataFrame(wifi_data).dropna(subset=["time"]).sort_values("time")
        for file_name in df_wifi["file"].unique():
            df_file = df_wifi[df_wifi["file"] == file_name]
            st.line_chart(df_file.set_index("time")["rssi"], height=300)
    else:
        st.warning("No WiFi RSSI data found in the uploaded files.")

    # --- SDM Traffic ---
    if sdm_data:
        st.subheader("SDM Traffic per second")
        df_sdm = pd.DataFrame(sdm_data).dropna(subset=["time"])
        df_sdm["second"] = df_sdm["time"].dt.floor("S")
        df_sdm_sec = df_sdm.groupby(["second", "direction"])["bytes"].sum().unstack(fill_value=0)
        df_sdm_sec["Total"] = df_sdm_sec.sum(axis=1)
        st.line_chart(df_sdm_sec, height=300)
    else:
        st.warning("No SDM Data found in the uploaded files.")

    # --- WAN connectivity ---
    if wan_data:
        st.subheader("WAN Connectivity over time")
        df_wan = pd.DataFrame(wan_data).dropna(subset=["time"]).sort_values("time")
        for file_name in df_wan["file"].unique():
            df_file = df_wan[df_wan["file"] == file_name]
            df_file_plot = pd.get_dummies(df_file.set_index("time")["wan"])
            st.line_chart(df_file_plot, height=200)
    else:
        st.warning("No WAN connectivity data found.")

    # --- Telemetry ---
    if telemetry_data:
        st.subheader("Telemetry send success/failure over time")
        df_tele = pd.DataFrame(telemetry_data).dropna(subset=["time"]).sort_values("time")
        for file_name in df_tele["file"].unique():
            df_file = df_tele[df_tele["file"] == file_name]
            # Показуємо Success зеленим, Failure червоним
            df_plot = df_file.set_index("time")[["success"]]
            df_plot["Success"] = df_plot["success"].apply(lambda x: x if x == 1 else None)
            df_plot["Failure"] = df_plot["success"].apply(lambda x: x if x == 0 else None)
            st.line_chart(df_plot[["Success", "Failure"]], height=200)
    else:
        st.warning("No telemetry data found.")

    # --- Call / Talkgroup activity (кількість подій на хвилину) ---
    if call_data:
        st.subheader("Call / Talkgroup activity over time (count per minute)")
        df_call = pd.DataFrame(call_data).dropna(subset=["time"])
        if not df_call.empty:
            # Групуємо по хвилинах
            df_call["minute"] = df_call["time"].dt.floor("T")
            # Підрахунок кількості подій по файлу
            df_call_count = df_call.groupby(["file", "minute"]).size().unstack(level=0, fill_value=0)
            st.line_chart(df_call_count, height=300)
    else:
        st.warning("No call/talkgroup activity found.")
