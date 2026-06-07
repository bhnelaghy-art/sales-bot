import streamlit as st
import requests
import re
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- 1. الإعدادات الأساسية وتنسيق الواجهة ---
st.set_page_config(page_title="نظام تسجيل العملاء", page_icon="🎯", layout="centered")

st.markdown("""
    <style>
        .main { direction: rtl; text-align: right; }
        .stButton>button { width: 100%; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. الإعدادات والربط ---
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
    SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
    GCP_CREDENTIALS = json.loads(st.secrets["GCP_CREDENTIALS"])
except Exception as e:
    st.error("خطأ في إعدادات النظام: تأكد من ضبط الـ Secrets.")
    st.stop()

# --- 3. الدوال الأساسية ---
def get_service():
    creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return build("sheets", "v4", credentials=creds)

def get_existing_data():
    try:
        service = get_service()
        sheet_name = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()['sheets'][0]['properties']['title']
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:B").execute()
        rows = result.get('values', [])
        names = {row[0].strip().lower() for row in rows if len(row) > 0}
        phones = {row[1].strip() for row in rows if len(row) > 1}
        return names, phones
    except: return set(), set()

def append_to_sheet(name, phone):
    try:
        service = get_service()
        sheet_name = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()['sheets'][0]['properties']['title']
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:C",
            valueInputOption="RAW", body={"values": [[name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]}
        ).execute()
        return True
    except: return False

# --- 4. لوحة الإدارة (Sidebar) ---
with st.sidebar:
    st.title("⚙️ لوحة الإدارة")
    password = st.text_input("كلمة المرور:", type="password")
    if password == "1234":
        names, phones = get_existing_data()
        st.metric("إجمالي العملاء", len(names))
        if st.button("تحديث البيانات"): st.rerun()
    else: st.warning("أدخل كلمة المرور لعرض الإحصائيات")
    
    st.divider()
    if st.button("🔄 بدء جلسة جديدة"):
        st.session_state.clear()
        st.rerun()

# --- 5. واجهة البوت التفاعلية ---
st.title("🎯 مساعد المبيعات الذكي")

if "step" not in st.session_state: st.session_state.step = "ask_name"
if "messages" not in st.session_state: 
    st.session_state.messages = [{"role": "assistant", "content": "أهلاً بك! أنا مساعدك الذكي. ما هو اسمك الكريم؟"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"]=="assistant" else "👤"):
        st.markdown(msg["content"])

if user_input := st.chat_input("اكتب هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"): st.markdown(user_input)
    
    with st.chat_message("assistant", avatar="🤖"):
        if st.session_state.step == "ask_name":
            st.session_state.temp_name = user_input
            st.session_state.step = "ask_phone"
            resp = f"تشرفنا يا {user_input.split()[0]}! من فضلك، ما هو رقم هاتفك؟"
        else:
            phone = re.sub(r'\D', '', user_input)
            if len(phone) == 11 and phone.startswith(('010', '011', '012', '015')):
                with st.spinner("جاري تأمين بياناتك..."):
                    if append_to_sheet(st.session_state.temp_name, phone):
                        resp = "✅ تم حفظ بياناتك بنجاح! سنتواصل معك قريباً."
                        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                                     params={"chat_id": TELEGRAM_CHAT_ID, "text": f"🎯 عميل جديد!\nالاسم: {st.session_state.temp_name}\nالهاتف: {phone}"})
                    else: resp = "⚠️ خطأ تقني، حاول مجدداً."
                st.session_state.step = "ask_name"
            else: resp = "❌ رقم غير صحيح. يرجى إدخال رقم مصري (11 رقماً) يبدأ بـ 010 أو 011 أو 012 أو 015."
        
        st.markdown(resp)
        st.session_state.messages.append({"role": "assistant", "content": resp})
