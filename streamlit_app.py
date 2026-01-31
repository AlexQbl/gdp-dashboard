import streamlit as st
import pandas as pd
import re
import json
import plotly.express as px

st.title("Multi-log Analyzer")

# Дозволяємо завантажити до 3 файлів одночасно
uploaded_files = st.file_uploader("Upload up to 3 log files", type=["log", "txt"], accept_multiple_files=True)

if uploaded_files:
    all_gps_points = []
    summary_data = []

    for uploaded_file in uploaded_files:
        # Спроба прочитати файл з автоматичним визначенням кодування
        try:
            log_text = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            try:
                log_text = uploaded_file.read().decode("latin1")
            except:
                st.error(f"Cannot decode file {uploaded_file.name}")
                continue

        gps_points = []

        # Регулярний вираз для пошуку JSON рядків з GPS
        json_pattern = re.compile(r'\{.*"gps":.*\}')

        for line in log_text.splitlines():
            match = json_pattern.search(line)
            if match:
                try:
                    data = json.loads(match.group())
                    gps = data.get("gps", {})
                    if gps.get("fix") and gps.get("latitude") and gps.get("longitude"):
                        gps_points.append({
                            "latitude": gps.get("latitude"),
                            "longitude": gps.get("longitude"),
                            "altitude": gps.get("altitude", None),
                            "timestamp": gps.get("tssec", None),
                            "file": uploaded_file.name
                        })
                except json.JSONDecodeError:
                    continue

        all_gps_points.extend(gps_points)

        # Додатково: можна зберегти інші дані для аналізу
        summary_data.append({
            "file": uploaded_file.name,
            "gps_points": len(gps_points)
        })

    st.write("GPS points extracted per file:")
    st.dataframe(pd.DataFrame(summary_data))

    if all_gps_points:
        gps_df = pd.DataFrame(all_gps_points)
        st.write(f"Total GPS points: {len(gps_df)}")

        # Карта Plotly
        fig = px.scatter_mapbox(
            gps_df,
            lat="latitude",
            lon="longitude",
            hover_data=["altitude", "timestamp", "file"],
            color="file",
            zoom=5,
            height=500
        )
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig)
    else:
        st.warning("No GPS points found in uploaded files.")