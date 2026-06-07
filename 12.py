import streamlit as st
import requests
import re
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- ضبط الواجهة لليمين ---
st.set_page_config(layout="wide")
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { direction: rtl; text-align: right; }
        [data-testid="stSidebar"] { direction: rtl; }
    </style>
""", unsafe_allow_html=True)

# 1. إعدادات الـ Secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
GCP_CREDENTIALS = json.loads(st.secrets["GCP_CREDENTIALS"])

# 2. تعريف الدوال
def get_sheet_name(service):
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    return spreadsheet['sheets'][0]['properties']['title']

def get_existing_data():
    try:
        creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
        service = build("sheets", "v4", credentials=creds)
        sheet_name = get_sheet_name(service)
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:B").execute()
        rows = result.get('values', [])
        names = {row[0].strip().lower() for row in rows if len(row) > 0}
        phones = {row[1].strip() for row in rows if len(row) > 1}
        return names, phones
    except:
        return set(), set()

def append_to_sheet(name, phone):
    try:
        creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = build("sheets", "v4", credentials=creds)
        sheet_name = get_sheet_name(service)
        values = [[name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:C",
            valueInputOption="RAW", body={"values": values}
        ).execute()
        return True
    except Exception as e:
        st.error(f"خطأ تقني: {e}")
        return False

def send_telegram_alert(name, phone):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🎯 عميل جديد!\nالاسم: {name}\nالرقم: {phone}"}
        requests.get(url, params=params)
        return True
    except: return False

# 3. لوحة التحكم الجانبية
with st.sidebar:
    st.header("⚙️ لوحة تحكم المدير")
    password = st.text_input("كلمة مرور المدير:", type="password")
    if password == "1234":
        st.success("أهلاً بك يا مدير!")
        names, phones = get_existing_data()
        st.metric("إجمالي العملاء", len(names))
        if st.button("عرض آخر 5 سجلات"):
            # ... كود عرض الجدول ...
            st.write("تم عرض السجلات")
    else:
        st.warning("أدخل كلمة المرور لعرض الإحصائيات")

# 4. الواجهة الرئيسية
st.title("🎯 نظام تسجيل العملاء")
# ... باقي الكود ...
