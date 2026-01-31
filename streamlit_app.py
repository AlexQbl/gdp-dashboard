import streamlit as st
import json
import pandas as pd
from datetime import datetime

st.title("Multi-log GPS & WiFi RSSI Visualizer")

uploaded_files = st.file_uploader(
    "Upload up to 3 log files", type=["log", "txt"], accept_multiple_files=True
)

if uploaded_files:
    all_gps_points = []
    summary_data = []
    wifi_data = []

    for uploaded_file in uploaded_files:
        try:
            log_text = uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception as e:
            st.error(f"Failed to read file {uploaded_file.name}: {e}")
            continue

        gps_points = []

        for line in log_text.splitlines():
            if '{"status"' in line:
                try:
                    json_part = line[line.index("{"):]
                    j = json.loads(json_part)

                    # --- GPS ---
                    gps = j.get("gps", {})
                    if gps.get("fix") and "latitude" in gps and "longitude" in gps:
                        gps_points.append({
                            "lat": gps["latitude"],
                            "lon": gps["longitude"],
                            "file": uploaded_file.name
                        })

                    # --- WiFi RSSI ---
                    wlan = j.get("wlanAsClientStatus", {})
                    rssi = wlan.get("rssi")
                    utc_time = gps.get("utc")  # час у форматі HHMMSS.s
                    date = gps.get("date")     # дата у форматі DDMMYY

                    if rssi is not None and utc_time and date:
                        # Конвертуємо у datetime
                        try:
                            dt_str = f"{date} {utc_time}"
                            dt = datetime.strptime(dt_str, "%d%m%y %H%M%S.%f")
                        except Exception:
                            dt = None
                        wifi_data.append({
                            "time": dt,
                            "rssi": rssi,
                            "file": uploaded_file.name
                        })

                except Exception:
                    continue

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
        df = pd.DataFrame(all_gps_points)
        st.map(df[["lat", "lon"]])
    else:
        st.warning("No GPS points found in the uploaded files.")

    # --- Вивід WiFi RSSI ---
    if wifi_data:
        st.subheader("WiFi RSSI over time")
        df_wifi = pd.DataFrame(wifi_data)
        df_wifi = df_wifi.dropna(subset=["time"])
        df_wifi = df_wifi.sort_values("time")

        for file_name in df_wifi["file"].unique():
            df_file = df_wifi[df_wifi["file"] == file_name]
            st.line_chart(df_file.set_index("time")["rssi"], height=300)
    else:
        st.warning("No WiFi RSSI data found in the uploaded files.")