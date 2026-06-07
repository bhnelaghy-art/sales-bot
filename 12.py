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
st.title("🎯 بوت المبيعات الذكي (مستوى احترافي)")

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    if "DATA_CAPTURE:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        
        # تعليمات صارمة للموديل الأذكى
        system_prompt = """أنت مساعد مبيعات محترف.
        1. لا تطلب البيانات إلا إذا وافق العميل على الشراء.
        2. عند توفر الاسم والرقم، اكتب فقط: DATA_CAPTURE: {"name": "الاسم", "phone": "الرقم"}
        3. تحذير: لا ترسل DATA_CAPTURE نهائياً إذا كانت البيانات غير مكتملة أو غير واضحة."""
        
        conversation = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        # استخدام الموديل الأقوى llama3-70b
        response = client.chat.completions.create(
            model="llama3-70b-8192", 
            messages=conversation, 
            temperature=0.1
        ).choices[0].message.content
        
        # معالجة JSON مع تنظيف إضافي
        if "DATA_CAPTURE:" in response:
            try:
                json_part = response.split("DATA_CAPTURE:")[1].strip()
                data = json.loads(json_part) 
                name = str(data.get("name", "")).strip()
                phone = str(data.get("phone", "")).strip()
                
                # شرط التحقق قبل الإرسال
                if len(name) > 1 and len(phone) >= 7:
                    send_telegram_alert(name, phone)
                    st.toast("✅ تم تسجيل بيانات العميل بنجاح!")
            except: 
                pass
            
            # تنظيف رد البوت
            response = response.split("DATA_CAPTURE:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
