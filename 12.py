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
    if "DATA_CAPTURE:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        # تعليمات للبوت عشان يعرف إمتى يطلب البيانات
        system_prompt = "أنت مساعد مبيعات. إذا وافق العميل، اطلب الاسم والرقم واكتب في نهاية رسالتك: DATA_CAPTURE: [الاسم] | [الرقم]"
        conversation = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=conversation, temperature=0.1).choices[0].message.content
        
        # معالجة البيانات وإرسال التليجرام
        if "DATA_CAPTURE:" in response:
            try:
                data = response.split("DATA_CAPTURE:")[1].replace("[","").replace("]","").split("|")
                name, phone = data[0].strip(), data[1].strip()
                send_telegram_alert(name, phone)
                st.toast("✅ تم إرسال بيانات العميل إليك على تليجرام!")
            except: pass
            response = response.split("DATA_CAPTURE:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
