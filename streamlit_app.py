import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.title("GPS Dashboard from Logs")

uploaded_file = st.file_uploader("Upload log file", type=["log","txt"])

if uploaded_file is not None:
    log_text = uploaded_file.read().decode("utf-8")
    lines = log_text.splitlines()

    gps_data = []

    for line in lines:
        # шукаємо рядки, які містять JSON
        if "{" in line and "}" in line:
            try:
                # беремо тільки частину з JSON
                json_part = line[line.index("{"):line.rindex("}")+1]
                obj = json.loads(json_part)
                gps = obj.get("gps", {})
                if gps.get("fix", 0) > 0:  # беремо тільки фіксовані GPS
                    gps_data.append({
                        "latitude": gps.get("latitude"),
                        "longitude": gps.get("longitude"),
                        "altitude": gps.get("altitude"),
                        "hdop": gps.get("hdop"),
                        "timestamp": gps.get("tssec")
                    })
            except json.JSONDecodeError:
                continue

    if gps_data:
        df = pd.DataFrame(gps_data)
        st.write("Sample GPS data:", df.head())

        fig_map = px.scatter_mapbox(
            df,
            lat="latitude",
            lon="longitude",
            size_max=15,
            zoom=10,
            hover_data=["altitude", "hdop", "timestamp"]
        )
        fig_map.update_layout(mapbox_style="open-street-map", height=500)
        st.plotly_chart(fig_map)
    else:
        st.warning("No valid GPS data found")