import streamlit as st
from groq import Groq
import json
import requests  # مكتبة جديدة للربط مع تليجرام
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# إعدادات الربط من الـ Secrets
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GCP_CREDENTIALS = json.loads(st.secrets["GCP_CREDENTIALS"])
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# قراءة ملف المعرفة
with open("knowledge.txt", "r", encoding="utf-8") as f:
    knowledge_base = f.read()

# تعريف الـ system_prompt
system_prompt = f"""
أنت وحش المبيعات المحترف. 
معلومات الكورس التي يجب أن تلتزم بها هي:
{knowledge_base}

1. السعر ثابت كما في المعلومات.
2. إذا وافق العميل، اطلب منه (الاسم ورقم الواتساب).
3. بمجرد الحصول على البيانات، اكتب هذا الكود في آخر سطر فقط:
DATA_CAPTURE: [الاسم] | [الرقم]
"""

# دالة إرسال تنبيه لتليجرام
def send_telegram_alert(name, phone):
    message = f"🎯 عميل جديد اشترى!\n\nالاسم: {name}\nالرقم: {phone}\nالتوقيت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    requests.get(url)

# دالة تسجيل البيانات في الشيت
def append_to_sheet(name, phone):
    try:
        creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = build("sheets", "v4", credentials=creds)
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_name = spreadsheet['sheets'][0]['properties']['title']
        
        values = [[name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:C",
            valueInputOption="RAW",
            body={"values": values}
        ).execute()
        
        # بعد التسجيل، نرسل التنبيه
        send_telegram_alert(name, phone)
        return True
    except Exception as e:
        st.error(f"خطأ في الشيت: {e}")
        return False

# واجهة المستخدم
st.set_page_config(page_title="منظومة المبيعات الذكية", page_icon="🎯", layout="centered")
st.markdown("""<style>.stApp { direction: RTL; text-align: right; } div[data-testid="stChatMessage"] { direction: RTL !important; text-align: right !important; }</style>""", unsafe_allow_html=True)

st.title("🎯 منظومة المبيعات الذكية")

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    if "DATA_CAPTURE:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    conversation = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=conversation, temperature=0.1)
        full_response = completion.choices[0].message.content
        
        if "DATA_CAPTURE:" in full_response:
            try:
                data = full_response.split("DATA_CAPTURE:")[1].strip()
                parts = data.split("|")
                if len(parts) >= 2:
                    name = parts[0].strip("[] ")
                    phone = parts[1].strip("[] ")
                    if append_to_sheet(name, phone):
                        st.toast("✅ تم تسجيل بيانات العميل وإرسال التنبيه!", icon="🎯")
            except: pass
            full_response = full_response.split("DATA_CAPTURE:")[0].strip()
            
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
