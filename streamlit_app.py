import streamlit as st
import json
import pandas as pd
import pydeck as pdk

st.title("GPS Map from Log File")

uploaded_file = st.file_uploader("Upload your log file", type=["log", "txt"])

if uploaded_file:
    # Читаємо файл і ігноруємо некоректні символи
    log_text = uploaded_file.read().decode("utf-8", errors="ignore")
    lines = log_text.split("\n")

    gps_data = []

    for line in lines:
        if "{" in line and "}" in line:
            try:
                # Витягуємо JSON частину
                json_part = line[line.index("{"):line.rindex("}")+1]
                obj = json.loads(json_part)
                gps = obj.get("gps", {})
                if gps.get("fix", 0) > 0:
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

        st.write("GPS points extracted:", len(df))

        # Відображаємо карту через pydeck
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v10',
            initial_view_state=pdk.ViewState(
                latitude=df['latitude'].mean(),
                longitude=df['longitude'].mean(),
                zoom=10,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df,
                    get_position='[longitude, latitude]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=50,
                ),
            ],
        ))
    else:
        st.warning("No valid GPS points found in the log.")