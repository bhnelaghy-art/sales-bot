import streamlit as st
import requests
import re

# إعدادات الـ Secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

if "registered_clients" not in st.session_state:
    st.session_state.registered_clients = []

# دالة إرسال التنبيه (تشتغل فقط إذا اكتملت الشروط)
def send_telegram_alert(name, phone):
    try:
        msg = f"🎯 عميل جديد!\nالاسم: {name}\nالرقم: {phone}"
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     params={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        return True
    except: return False

st.title("🎯 بوت التسجيل (نظام صارم)")

if "step" not in st.session_state: st.session_state.step = "ask_name"
if "temp_name" not in st.session_state: st.session_state.temp_name = ""
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("تفضل..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        # الخطوة 1: طلب الاسم الثلاثي (إجباري)
        if st.session_state.step == "ask_name":
            # التحقق: هل المدخل اسم ثلاثي؟
            if len(user_input.split()) >= 3:
                st.session_state.temp_name = user_input.strip()
                st.session_state.step = "ask_phone"
                response = "شكراً، تم حفظ الاسم. من فضلك اكتب رقم الموبايل الآن للتسجيل."
            else:
                response = "عذراً، يرجى كتابة الاسم الثلاثي بالكامل للمتابعة."

        # الخطوة 2: طلب الرقم (إجباري)
        elif st.session_state.step == "ask_phone":
            phone_clean = re.sub(r'\D', '', user_input)
            
            # التحقق: هل الرقم مصري وسليم؟
            if len(phone_clean) == 11 and phone_clean.startswith(('010', '011', '012', '015')):
                
                # التحقق: هل مكرر؟
                client_id = f"{st.session_state.temp_name.lower()}|{phone_clean}"
                if client_id in st.session_state.registered_clients:
                    response = "هذا الاسم وهذا الرقم مسجلان مسبقاً. العملية مرفوضة."
                    st.session_state.step = "ask_name"
                else:
                    if send_telegram_alert(st.session_state.temp_name, phone_clean):
                        st.session_state.registered_clients.append(client_id)
                        response = "تم تسجيلك بنجاح!"
                    else:
                        response = "خطأ في الاتصال، حاول لاحقاً."
                    st.session_state.step = "ask_name"
            else:
                response = "الرقم غير صحيح! يرجى إدخال رقم موبايل مصري مكون من 11 رقماً."

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
