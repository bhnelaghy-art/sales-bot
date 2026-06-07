import streamlit as st
import requests
from groq import Groq
import re

# إعدادات الـ Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# دالة إرسال التنبيه
def send_telegram_alert(name, phone):
    try:
        msg = f"🎯 عميل جديد (بيانات مكتملة)!\nالاسم: {name}\nالرقم: {phone}"
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        return True
    except: return False

st.title("🎯 بوت المبيعات (نظام الخطوتين)")

if "step" not in st.session_state: st.session_state.step = "ask_name"
if "temp_name" not in st.session_state: st.session_state.temp_name = ""
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("تفضل..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        # الخطوة 1: استلام الاسم الثلاثي
        if st.session_state.step == "ask_name":
            # التأكد أن الاسم مكون من 3 أجزاء
            if len(user_input.split()) >= 3:
                st.session_state.temp_name = user_input
                st.session_state.step = "ask_phone"
                response = "تمام يا فندم، سجلت الاسم. ممكن رقم موبايلك عشان نتواصل معاك؟"
            else:
                response = "ممكن تكتب الاسم الثلاثي بالكامل عشان أقدر أسجله بشكل صحيح؟"
        
        # الخطوة 2: استلام الرقم والتسجيل
        elif st.session_state.step == "ask_phone":
            phone_clean = re.sub(r'\D', '', user_input)
            if len(phone_clean) == 11 and phone_clean.startswith(('010', '011', '012', '015')):
                send_telegram_alert(st.session_state.temp_name, phone_clean)
                response = "شكراً لك! تم تسجيل بياناتك بنجاح وهنتواصل معاك في أقرب وقت."
                st.session_state.step = "ask_name" # إعادة الضبط للعميل القادم
            else:
                response = "الرقم غير صحيح، لازم رقم مصري (11 رقم). من فضلك أعد كتابة الرقم."

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
