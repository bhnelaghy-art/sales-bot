import streamlit as st
from groq import Groq
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# إعدادات الربط من الـ Secrets
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
# تحويل الـ JSON النصي الموجود في الـ Secrets إلى قاموس بيانات (Dictionary)
GCP_CREDENTIALS = json.loads(st.secrets["GCP_CREDENTIALS"])

def append_to_sheet(name, phone):
    try:
        # استخدام البيانات مباشرة بدلاً من الملف
        creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = build("sheets", "v4", credentials=creds)
        
        # جلب اسم أول ورقة في الشيت أوتوماتيكياً
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_name = spreadsheet['sheets'][0]['properties']['title']
        
        values = [[name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:C",
            valueInputOption="RAW",
            body={"values": values}
        ).execute()
        return True
    except Exception as e:
        st.error(f"خطأ في الشيت: {e}")
        return False

st.set_page_config(page_title="منظومة المبيعات الذكية", page_icon="🎯", layout="centered")
st.markdown("""<style>.stApp { direction: RTL; text-align: right; } div[data-testid="stChatMessage"] { direction: RTL !important; text-align: right !important; }</style>""", unsafe_allow_html=True)

st.title("🎯 منظومة المبيعات الذكية")

if "messages" not in st.session_state: st.session_state.messages = []

# عرض الرسائل
for msg in st.session_state.messages:
    if "DATA_CAPTURE:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    system_prompt = """
    أنت وحش المبيعات المحترف. 
    1. السعر النهائي للكورس 1799 جنيه مصري.
    2. إذا وافق العميل على الشراء، اطلب منه فوراً (الاسم ورقم الواتساب).
    3. بمجرد أن يعطيك البيانات، قم بتأكيد الحجز ثم أكتب في آخر سطر بالرسالة هذا الكود فقط:
    DATA_CAPTURE: [الاسم] | [الرقم]
    لا تكتب أي كلام بعد هذا الكود.
    """
    
    conversation = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=conversation, temperature=0.2)
        full_response = completion.choices[0].message.content
        
        if "DATA_CAPTURE:" in full_response:
            try:
                data = full_response.split("DATA_CAPTURE:")[1].strip()
                parts = data.split("|")
                if len(parts) >= 2:
                    name = parts[0].strip("[] ")
                    phone = parts[1].strip("[] ")
                    if append_to_sheet(name, phone):
                        st.toast("✅ تم تسجيل بيانات العميل في الشيت بنجاح!", icon="🎯")
            except: pass
            full_response = full_response.split("DATA_CAPTURE:")[0].strip()
            
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
