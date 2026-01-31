import streamlit as st
import json
import pandas as pd
from datetime import datetime
import re

st.title("GPS, SDM & Network Visualizer")

uploaded_files = st.file_uploader(
    "Upload up to 3 log files", type=["log", "txt"], accept_multiple_files=True
)

if uploaded_files:
    all_gps_points = []
    summary_data = []
    wifi_data = []
    sdm_data = []
    lte_data = []
    service_status_data = []

    for uploaded_file in uploaded_files:
        try:
            log_text = uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception as e:
            st.error(f"Failed to read file {uploaded_file.name}: {e}")
            continue

        gps_points = []
        last_gps_time = None

        for line in log_text.splitlines():
            # --- GPS та WiFi ---
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
                    if utc_time and date:
                        try:
                            dt_str = f"{date} {utc_time}"
                            dt = datetime.strptime(dt_str, "%d%m%y %H%M%S.%f")
                            last_gps_time = dt
                        except Exception:
                            dt = last_gps_time

                        if rssi is not None:
                            wifi_data.append({
                                "time": dt,
                                "rssi": rssi,
                                "file": uploaded_file.name
                            })

                    # LTE CSQ
                    lte_status = j.get("lteStatus", {})
                    csq = lte_status.get("csq")
                    if csq is not None and dt:
                        lte_data.append({
                            "time": dt,
                            "csq": csq,
                            "file": uploaded_file.name
                        })

                    # Service status
                    s_status = j.get("status", {})
                    for svc in ["lte", "wifiAp", "eth", "gps"]:
                        status_val = 1 if s_status.get(svc) else 0
                        service_status_data.append({
                            "time": dt,
                            "service": svc,
                            "status": status_val,
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

        all_gps_points.extend(gps_points)
        summary_data.append({
            "file": uploaded_file.name,
            "gps_points": len(gps_points)
        })

    # --- Вивід GPS ---
    st.subheader("GPS points extracted per file:")
    st.dataframe(pd.DataFrame(summary_data))

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

    # --- LTE Signal Quality ---
    if lte_data:
        st.subheader("LTE Signal Quality (CSQ) over time")
        df_lte = pd.DataFrame(lte_data).dropna(subset=["time"]).sort_values("time")
        for file_name in df_lte["file"].unique():
            df_file = df_lte[df_lte["file"] == file_name]
            st.line_chart(df_file.set_index("time")["csq"], height=300)
    else:
        st.warning("No LTE data found in the uploaded files.")

    # --- Service Status ---
    if service_status_data:
        st.subheader("Service Status over time (1=In Service, 0=Out of Service)")
        df_status = pd.DataFrame(service_status_data).dropna(subset=["time"])
        df_status["second"] = df_status["time"].dt.floor("S")
        df_status_sec = df_status.groupby(["second", "service"])["status"].max().unstack(fill_value=0)
        st.line_chart(df_status_sec, height=300)
    else:
        st.warning("No service status data found in the uploaded files.")
