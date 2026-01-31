import streamlit as st
import pandas as pd
import plotly.express as px
import re
import io

st.title("Лог-аналітика IVH/SDM")

# Завантаження файлу
uploaded_file = st.file_uploader("Завантажте лог-файл", type=["log", "txt"])

if uploaded_file is not None:
    # Читаємо файл як текст
    text_io = io.TextIOWrapper(uploaded_file, encoding="utf-8")
    log_text = text_io.read()

    # Рядки логів
    lines = log_text.splitlines()

    # Підготовка списку для DataFrame
    data = []

    # Регекспи для витягання метрик
    csq_re = re.compile(r"LTE CSQ:\s*(-?\d+)")
    rssi_re = re.compile(r"WIFI RSSI:\s*(-?\d+)")
    snr_re = re.compile(r"SATELLITE SNR:\s*(-?\d+)")
    thread_re = re.compile(r"thread count\((\d+)\)")

    time_re = re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4} \d{2}:\d{2}:\d{2})")

    for line in lines:
        timestamp_match = time_re.search(line)
        if timestamp_match:
            timestamp = timestamp_match.group(1)
        else:
            continue

        csq = csq_re.search(line)
        rssi = rssi_re.search(line)
        snr = snr_re.search(line)
        thread = thread_re.search(line)

        data.append({
            "timestamp": timestamp,
            "LTE_CSQ": int(csq.group(1)) if csq else None,
            "WiFi_RSSI": int(rssi.group(1)) if rssi else None,
            "Satellite_SNR": int(snr.group(1)) if snr else None,
            "Thread_Count": int(thread.group(1)) if thread else None
        })

    # Створення DataFrame
    df = pd.DataFrame(data)

    # Конвертація timestamp у datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d/%m/%y %H:%M:%S")

    st.subheader("Таблиця з витягнутими метриками")
    st.dataframe(df)

    # Побудова графіків
    metrics = ["LTE_CSQ", "WiFi_RSSI", "Satellite_SNR", "Thread_Count"]
    for metric in metrics:
        fig = px.line(df, x="timestamp", y=metric, title=f"{metric} по часу")
        st.plotly_chart(fig)