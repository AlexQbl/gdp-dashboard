import streamlit as st
import json
import pandas as pd

st.title("Multi-log GPS Visualizer")

uploaded_files = st.file_uploader("Upload up to 3 log files", type=["log", "txt"], accept_multiple_files=True)

if uploaded_files:
    all_gps_points = []
    summary_data = []

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
                    gps = j.get("gps", {})
                    if gps.get("fix") and "latitude" in gps and "longitude" in gps:
                        gps_points.append({
                            "lat": gps["latitude"],
                            "lon": gps["longitude"],
                            "file": uploaded_file.name
                        })
                except Exception:
                    continue

        all_gps_points.extend(gps_points)
        summary_data.append({
            "file": uploaded_file.name,
            "gps_points": len(gps_points)
        })

    st.write("GPS points extracted per file:")
    st.dataframe(pd.DataFrame(summary_data))

    if all_gps_points:
        df = pd.DataFrame(all_gps_points)
        st.write(f"Total GPS points: {len(df)}")
        st.map(df[["lat", "lon"]])
    else:
        st.warning("No GPS points found in the uploaded files.")
