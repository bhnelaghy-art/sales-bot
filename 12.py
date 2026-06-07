import streamlit as st
import requests
import re

# إعدادات الـ Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# تخزين السجلات (الأسماء والأرقام) لمنع التكرار
if "registered_clients" not in st.session_state:
    st.session_state.registered_clients = []

# دالة إرسال التنبيه
def send_telegram_alert(name, phone):
    try:
        msg = f"🎯 عميل جديد!\nالاسم: {name}\nالرقم: {phone}"
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        return True
    except: return False

st.title("🎯 بوت التسجيل (منع التكرار)")

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
            if len(user_input.split()) >= 3:
                st.session_state.temp_name = user_input.strip()
                st.session_state.step = "ask_phone"
                response = "تمام يا فندم، سجلت الاسم. ممكن رقم موبايلك؟"
            else:
                response = "من فضلك سجل الاسم الثلاثي بالكامل."
        
        # الخطوة 2: استلام الرقم والتحقق من التكرار
        elif st.session_state.step == "ask_phone":
            phone_clean = re.sub(r'\D', '', user_input)
            
            if len(phone_clean) == 11 and phone_clean.startswith(('010', '011', '012', '015')):
                # إنشاء بصمة فريدة للعميل
                client_id = f"{st.session_state.temp_name.lower()}|{phone_clean}"
                
                if client_id in st.session_state.registered_clients:
                    response = "عذراً، هذا الاسم وهذا الرقم مسجلان لدينا مسبقاً."
                    st.session_state.step = "ask_name"
                else:
                    if send_telegram_alert(st.session_state.temp_name, phone_clean):
                        st.session_state.registered_clients.append(client_id)
                        response = "شكراً! تم تسجيل بياناتك بنجاح."
                    else:
                        response = "حدث خطأ في الاتصال، يرجى المحاولة لاحقاً."
                    st.session_state.step = "ask_name" 
            else:
                response = "رقم غير صحيح، يرجى إدخال رقم مصري (11 رقم)."

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        
