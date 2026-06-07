import streamlit as st
import json
import requests
from datetime import datetime
from groq import Groq
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 1. إعدادات الـ Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
GCP_CREDENTIALS = json.loads(st.secrets["GCP_CREDENTIALS"])
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# 2. دالة إرسال التنبيه
def send_telegram_alert(name, phone):
    try:
        msg = f"🎯 عميل جديد! {name} | {phone}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={msg}"
        requests.get(url)
    except: pass

# 3. دالة تسجيل البيانات في الشيت (بشكل مباشر)
def append_to_sheet(name, phone):
    try:
        creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = build("sheets", "v4", credentials=creds)
        values = [[name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="A:C", # النطاق المباشر بدون اسم الشيت
            valueInputOption="RAW",
            body={"values": values}
        ).execute()
        send_telegram_alert(name, phone)
        return True
    except Exception as e:
        return str(e)

# 4. واجهة المستخدم
st.title("🎯 منظومة المبيعات الذكية")

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    if "DATA_CAPTURE:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        conversation = [{"role": "system", "content": "إذا وافق العميل، اطلب الاسم والرقم واكتب: DATA_CAPTURE: [الاسم] | [الرقم]"}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=conversation, temperature=0.1).choices[0].message.content
        
        if "DATA_CAPTURE:" in response:
            try:
                data = response.split("DATA_CAPTURE:")[1].replace("[","").replace("]","").split("|")
                res = append_to_sheet(data[0].strip(), data[1].strip())
                if res == True: st.toast("✅ تم تسجيل العميل وتنبيهك!")
                else: st.error(f"خطأ: {res}")
            except: pass
            response = response.split("DATA_CAPTURE:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
