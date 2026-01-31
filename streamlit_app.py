import streamlit as st
import json
import pandas as pd

st.title("GPS Log Visualizer")

uploaded_file = st.file_uploader("Upload log file", type=["log", "txt"])
if uploaded_file is not None:
    try:
        log_text = uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

    gps_points = []

    for line in log_text.splitlines():
        # шукаємо рядки, що містять JSON з GPS
        if '{"status"' in line:
            try:
                # Витягуємо частину після першого '{'
                json_part = line[line.index("{"):]
                j = json.loads(json_part)
                gps = j.get("gps", {})
                if gps.get("fix") and "latitude" in gps and "longitude" in gps:
                    gps_points.append((gps["latitude"], gps["longitude"]))
            except Exception:
                continue

    st.write(f"GPS points extracted: {len(gps_points)}")

    if gps_points:
        df = pd.DataFrame(gps_points, columns=["lat", "lon"])
        st.map(df)
    else:
        st.warning("No GPS points found in the log.")