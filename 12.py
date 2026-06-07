import streamlit as st
import requests
import json
from groq import Groq

# إعدادات الـ Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# دالة إرسال التنبيه لتليجرام
def send_telegram_alert(name, phone):
    try:
        msg = f"🎯 عميل جديد!\nالاسم: {name}\nالرقم: {phone}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        requests.get(url, params=params)
    except: pass

# واجهة الشات
st.title("🎯 بوت المبيعات الذكي")

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    if "DATA_CAPTURE:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        
        # تعليمات دقيقة لاستخدام JSON
        system_prompt = """أنت مساعد مبيعات محترف. 
        1. لا تطلب البيانات إلا إذا أبدى العميل رغبة حقيقية.
        2. عند توفر الاسم والرقم، اكتب فقط: DATA_CAPTURE: {"name": "الاسم هنا", "phone": "الرقم هنا"}
        3. التزم بتنسيق JSON بدقة، ولا تكتب أي نص إضافي بجوار DATA_CAPTURE."""
        
        conversation = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=conversation, temperature=0.1).choices[0].message.content
        
        # معالجة JSON لاستخراج البيانات
        if "DATA_CAPTURE:" in response:
            try:
                json_part = response.split("DATA_CAPTURE:")[1].strip()
                data = json.loads(json_part) 
                name = data.get("name", "")
                phone = data.get("phone", "")
                
                # التحقق من صحة البيانات قبل الإرسال
                if len(name) > 1 and len(phone) > 5:
                    send_telegram_alert(name, phone)
                    st.toast("✅ تم تسجيل بيانات العميل وإرسال التنبيه!")
            except: 
                pass
            
            # عرض رد البوت للعميل بدون كود الـ JSON
            response = response.split("DATA_CAPTURE:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
