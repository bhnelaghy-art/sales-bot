import streamlit as st
import requests
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
    if "CAPTURE_DATA:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        
        # تعليمات مبسطة للبوت (أسهل للموديلات الصغيرة)
        system_prompt = """أنت مساعد مبيعات. عندما يزودك العميل باسمه ورقم هاتفه، اكتب فقط هذه الصيغة:
        CAPTURE_DATA: الاسم | الرقم
        لا تكتب أي شيء آخر مع هذه الصيغة."""
        
        conversation = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        # استخدام الموديل المستقر والسريع
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=conversation, 
            temperature=0.1
        ).choices[0].message.content
        
        # معالجة البيانات بطريقة بسيطة ومضمونة
        if "CAPTURE_DATA:" in response:
            try:
                # استخراج البيانات من النص
                content = response.split("CAPTURE_DATA:")[1].strip()
                name, phone = content.split("|")
                
                # شرط التحقق (لا يرسل إلا لو البيانات حقيقية)
                if len(name.strip()) > 1 and len(phone.strip()) >= 7:
                    send_telegram_alert(name.strip(), phone.strip())
                    st.toast("✅ تم تسجيل بيانات العميل بنجاح!")
            except: 
                pass
            
            # تنظيف رد البوت
            response = response.split("CAPTURE_DATA:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
