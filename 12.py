import streamlit as st
import json
import requests
from datetime import datetime
from groq import Groq
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# إعدادات الـ Secrets
try:
    SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GCP_CREDENTIALS = json.loads(st.secrets["GCP_CREDENTIALS"])
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except Exception as e:
    st.error(f"خطأ في تحميل البيانات السرية: {e}")
    st.stop() # إيقاف البوت لو الـ Secrets مش موجودة

st.title("🎯 منظومة المبيعات الذكية")
st.write("البوت يعمل الآن ومربوط بقاعدة البيانات!")
