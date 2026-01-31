import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re
import json

st.title("GPS Log Visualizer")

# Завантаження файлу
uploaded_file = st.file_uploader("Завантаж файл логів", type=["log", "txt"])

if uploaded_file:
    try:
        # Читаємо файл у текст
        log_text = uploaded_file.read().decode("utf-8", errors="ignore")

        # Витягаємо JSON об'єкти зі строк
        json_matches = re.findall(r'(\{.*?\})', log_text, re.DOTALL)
        gps_data = []

        for jm in json_matches:
            try:
                obj = json.loads(jm)
                if "gps" in obj:
                    gps = obj["gps"]
                    if gps.get("fix", 0) > 0:  # тільки якщо GPS зафіксовано
                        gps_data.append({
                            "latitude": gps.get("latitude"),
                            "longitude": gps.get("longitude"),
                            "altitude": gps.get("altitude"),
                            "tssec": gps.get("tssec")
                        })
            except Exception as e:
                continue  # ігноруємо помилки JSON

        st.write(f"GPS points extracted: {len(gps_data)}")

        if gps_data:
            df = pd.DataFrame(gps_data)

            # Середня точка для центру карти
            center_lat = df['latitude'].mean()
            center_lon = df['longitude'].mean()

            # Створюємо карту
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

            # Додаємо маркери
            for _, row in df.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=5,
                    color='red',
                    fill=True,
                    fill_opacity=0.7,
                    popup=f"Alt: {row['altitude']} m, TS: {row['tssec']}"
                ).add_to(m)

            # Відображаємо карту у Streamlit
            st_folium(m, width=700, height=500)
        else:
            st.warning("Не знайдено GPS точок у файлі.")

    except Exception as e:
        st.error(f"Помилка обробки файлу: {e}")
