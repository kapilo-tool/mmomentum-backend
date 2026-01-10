import streamlit as st
import requests

API_URL = "https://mmomentum-backend.onrender.com"

st.set_page_config(page_title="M-Momentum Tool", layout="centered")

st.title("📈 M-Momentum Score Tool")

symbol = st.text_input("Aktien-Symbol eingeben:", value="AAPL")

if st.button("Score berechnen"):
    with st.spinner("Berechne Score..."):
        try:
            response = requests.get(f"{API_URL}/score", params={"symbol": symbol})
            data = response.json()

            st.success("Score erfolgreich berechnet!")
            st.write("### Ergebnis")
            st.json(data)

        except Exception as e:
            st.error("Fehler beim Abrufen des Scores")
            st.write(e)
