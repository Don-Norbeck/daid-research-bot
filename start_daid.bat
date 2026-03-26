@echo off
cd /d C:\Users\donal\OneDrive\Documents\daid-research-bot
start "" "C:\Program Files\Python312\python.exe" -m streamlit run app.py
timeout /t 2 >nul
start "" "http://localhost:8501"