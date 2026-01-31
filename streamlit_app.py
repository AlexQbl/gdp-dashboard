# log_dashboard.py
import re
import json
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="IVH Log Dashboard", layout="wide")
st.title("IVH Log Dashboard")

# --- Завантаження файлу ---
uploaded_file = st.file_uploader("Завантаж лог файл", type=["log", "txt"])
if uploaded_file is not None:
    log_text = uploaded_file.read().decode("utf-8")
    
    # --- Регулярні вирази для парсингу ---
    lte_re = re.compile(r"LTE CSQ:\s*(-?\d+)")
    wifi_re = re.compile(r"WIFI RSSI:\s*(-?\d+)")
    sat_re = re.compile(r"SATELLITE SNR:\s*(\d+)")
    thread_re = re.compile(r"thread count\((\d+)\)")
    error_re = re.compile(r"error count\((\d+)\)")
    time_re = re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4} \d{2}:\d{2}:\d{2})")
    
    # --- Парсинг ---
    times = []
    lte_vals = []
    wifi_vals = []
    sat_vals = []
    thread_vals = []
    error_vals = []

    for line in log_text.splitlines():
        time_match = time_re.search(line)
        if time_match:
            times.append(pd.to_datetime(time_match.group(1), format="%d/%m/%y %H:%M:%S"))
        else:
            # Якщо немає часу, повторюємо останній
            times.append(times[-1] if times else pd.Timestamp.now())
        
        lte_vals.append(int(lte_re.search(line).group(1)) if lte_re.search(line) else None)
        wifi_vals.append(int(wifi_re.search(line).group(1)) if wifi_re.search(line) else None)
        sat_vals.append(int(sat_re.search(line).group(1)) if sat_re.search(line) else None)
        thread_vals.append(int(thread_re.search(line).group(1)) if thread_re.search(line) else None)
        error_vals.append(int(error_re.search(line).group(1)) if error_re.search(line) else None)

    # --- DataFrame ---
    df = pd.DataFrame({
        "Time": times,
        "LTE CSQ": lte_vals,
        "WiFi RSSI": wifi_vals,
        "Satellite SNR": sat_vals,
        "Thread Count": thread_vals,
        "Error Count": error_vals
    })

    st.subheader("Графіки сигналу")
    fig_signal = px.line(df, x="Time", y=["LTE CSQ", "WiFi RSSI", "Satellite SNR"], 
                         labels={"value":"Signal", "variable":"Type"}, 
                         title="LTE, WiFi та Satellite сигнали")
    st.plotly_chart(fig_signal, use_container_width=True)

    st.subheader("Графіки ресурсів")
    fig_resources = px.line(df, x="Time", y=["Thread Count", "Error Count"], 
                            labels={"value":"Count", "variable":"Resource"}, 
                            title="Thread та Error Count")
    st.plotly_chart(fig_resources, use_container_width=True)