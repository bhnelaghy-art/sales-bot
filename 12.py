import streamlit as st
import requests
import re
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# إعدادات الـ Secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
GCP_CREDENTIALS = json.loads(st.secrets["GCP_CREDENTIALS"])

# دالة لقراءة البيانات الموجودة في الشيت لمنع التكرار
def get_existing_data():
    try:
        creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1!A:B").execute()
        rows = result.get('values', [])
        names = {row[0].strip().lower() for row in rows if len(row) > 0}
        phones = {row[1].strip() for row in rows if len(row) > 1}
        return names, phones
    except:
        return set(), set()

# دالة إضافة البيانات للشيت مع كشف الأخطاء
def append_to_sheet(name, phone):
    try:
        creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = build("sheets", "v4", credentials=creds)
        values = [[name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A:C",
            valueInputOption="RAW", body={"values": values}
        ).execute()
        return True
    except Exception as e:
        st.error(f"خطأ تقني في الاتصال بـ Google Sheets: {e}")
        return False

# دالة إرسال التنبيه
def send_telegram_alert(name, phone):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🎯 عميل جديد!\nالاسم: {name}\nالرقم: {phone}"}
        requests.get(url, params=params)
        return True
    except: return False

st.title("🎯 نظام تسجيل العملاء (الربط المباشر مع الشيت)")

if "step" not in st.session_state: st.session_state.step = "ask_name"
if "temp_name" not in st.session_state: st.session_state.temp_name = ""
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("أدخل البيانات..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        response = ""
        existing_names, existing_phones = get_existing_data()
        
        if st.session_state.step == "ask_name":
            clean_name = user_input.strip().lower()
            
            if len(user_input.split()) < 3:
                response = "عذراً، يرجى إدخال الاسم الثلاثي بالكامل."
            elif clean_name in existing_names:
                response = "هذا الاسم مسجل لدينا مسبقاً في قاعدة البيانات."
            else:
                st.session_state.temp_name = user_input.strip()
                st.session_state.step = "ask_phone"
                response = "تم حفظ الاسم. من فضلك الآن أرسل رقم الهاتف (11 رقم)."

        elif st.session_state.step == "ask_phone":
            phone_clean = re.sub(r'\D', '', user_input)
            
            if len(phone_clean) != 11 or not phone_clean.startswith(('010', '011', '012', '015')):
                response = "الرقم غير صحيح! أعد كتابة رقم مصري مكون من 11 رقماً."
            elif phone_clean in existing_phones:
                response = "هذا الرقم مسجل مسبقاً في نظامنا."
                st.session_state.step = "ask_name"
            else:
                if append_to_sheet(st.session_state.temp_name, phone_clean):
                    send_telegram_alert(st.session_state.temp_name, phone_clean)
                    response = "✅ تم التسجيل بنجاح وتم حفظ البيانات في الشيت!"
                else:
                    response = "تعذر التسجيل بسبب خطأ في قاعدة البيانات."
                st.session_state.step = "ask_name"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
