import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.title("Log Analysis Dashboard with GPS Map")

# Завантаження файлу
uploaded_file = st.file_uploader("Upload log file", type=["log", "txt"])

if uploaded_file is not None:
    # Читаємо файл як байти та декодуємо, ігноруючи некоректні символи
    bytes_data = uploaded_file.read()
    log_text = bytes_data.decode("utf-8", errors="ignore")
    
    # Розбиваємо на рядки
    lines = log_text.splitlines()
    
    # Дані для графіків
    data = {
        "timestamp": [],
        "LTE_CSQ": [],
        "WiFi_RSSI": [],
        "Satellite_SNR": [],
        "thread_count": [],
        "error_count": [],
        "latitude": [],
        "longitude": []
    }

    # Регулярні вирази для парсингу
    timestamp_re = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4} \d{2}:\d{2}:\d{2})')
    lte_re = re.compile(r'LTE CSQ:\s*(-?\d+)')
    wifi_re = re.compile(r'WIFI RSSI:\s*(-?\d+)')
    sat_re = re.compile(r'SATELLITE SNR:\s*(\d+)')
    pasource_re = re.compile(r'PASource:.*thread count\((\d+)\).*error count\((\d+)\)')
    gps_re = re.compile(r'LAT:\s*(-?\d+\.\d+)\s+LON:\s*(-?\d+\.\d+)')

    for line in lines:
        ts_match = timestamp_re.search(line)
        if ts_match:
            ts = ts_match.group(1)
        else:
            continue  # Якщо рядок без таймштампу — пропускаємо

        # Парсимо дані
        lte_match = lte_re.search(line)
        wifi_match = wifi_re.search(line)
        sat_match = sat_re.search(line)
        pasource_match = pasource_re.search(line)
        gps_match = gps_re.search(line)

        data["timestamp"].append(ts)
        data["LTE_CSQ"].append(int(lte_match.group(1)) if lte_match else None)
        data["WiFi_RSSI"].append(int(wifi_match.group(1)) if wifi_match else None)
        data["Satellite_SNR"].append(int(sat_match.group(1)) if sat_match else None)
        if pasource_match:
            data["thread_count"].append(int(pasource_match.group(1)))
            data["error_count"].append(int(pasource_match.group(2)))
        else:
            data["thread_count"].append(None)
            data["error_count"].append(None)
        if gps_match:
            data["latitude"].append(float(gps_match.group(1)))
            data["longitude"].append(float(gps_match.group(2)))
        else:
            data["latitude"].append(None)
            data["longitude"].append(None)

    # Перетворимо у DataFrame
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d/%m/%y %H:%M:%S")

    st.subheader("Raw Data Sample")
    st.dataframe(df.head(20))

    # Графіки сигналу
    st.subheader("LTE CSQ over Time")
    fig1 = px.line(df, x="timestamp", y="LTE_CSQ", title="LTE Signal Strength (CSQ)")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("WiFi RSSI over Time")
    fig2 = px.line(df, x="timestamp", y="WiFi_RSSI", title="WiFi Signal Strength (RSSI)")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Satellite SNR over Time")
    fig3 = px.line(df, x="timestamp", y="Satellite_SNR", title="Satellite SNR")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Thread Count and Error Count over Time")
    fig4 = px.line(df, x="timestamp", y=["thread_count", "error_count"], title="Thread & Error Counts")
    st.plotly_chart(fig4, use_container_width=True)

    # Карта GPS, якщо є координати
    if df["latitude"].notna().any() and df["longitude"].notna().any():
        st.subheader("GPS Map")
        gps_df = df.dropna(subset=["latitude", "longitude"])
        fig_map = px.scatter_mapbox(
            gps_df,
            lat="latitude",
            lon="longitude",
            color="LTE_CSQ",
            size="LTE_CSQ",
            hover_data=["timestamp", "WiFi_RSSI", "Satellite_SNR"],
            zoom=10,
            height=500
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig_map, use_container_width=True)