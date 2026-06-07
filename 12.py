import streamlit as st
import requests
import re

# إعدادات الـ Secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

if "registered_clients" not in st.session_state:
    st.session_state.registered_clients = []

# دالة إرسال التنبيه
def send_telegram_alert(name, phone):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🎯 عميل جديد!\nالاسم: {name}\nالرقم: {phone}"}
        requests.get(url, params=params)
        return True
    except: return False

st.title("🎯 نظام تسجيل العملاء الصارم")

if "step" not in st.session_state: st.session_state.step = "ask_name"
if "temp_name" not in st.session_state: st.session_state.temp_name = ""
if "messages" not in st.session_state: st.session_state.messages = []

# عرض الرسائل السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("أدخل البيانات..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        response = ""
        
        # --- المنطق البرمجي الصارم (لا يعتمد على الذكاء الاصطناعي) ---
        
        if st.session_state.step == "ask_name":
            # التحقق: هل هو اسم ثلاثي؟
            if len(user_input.split()) >= 3:
                st.session_state.temp_name = user_input.strip()
                st.session_state.step = "ask_phone"
                response = "تم حفظ الاسم. من فضلك الآن أرسل رقم الهاتف (11 رقم)."
            else:
                response = "عفواً، يجب إدخال الاسم الثلاثي بالكامل (3 كلمات على الأقل)."
                
        elif st.session_state.step == "ask_phone":
            phone_clean = re.sub(r'\D', '', user_input)
            
            # التحقق: هل الرقم مصري؟
            if len(phone_clean) == 11 and phone_clean.startswith(('010', '011', '012', '015')):
                client_id = f"{st.session_state.temp_name.lower()}|{phone_clean}"
                
                # التحقق: هل مكرر؟
                if client_id in st.session_state.registered_clients:
                    response = "هذا العميل مسجل مسبقاً! جاري إعادة البدء."
                    st.session_state.step = "ask_name"
                else:
                    if send_telegram_alert(st.session_state.temp_name, phone_clean):
                        st.session_state.registered_clients.append(client_id)
                        response = "✅ تم التسجيل بنجاح!"
                    else:
                        response = "خطأ في الاتصال بالسيرفر."
                    st.session_state.step = "ask_name"
            else:
                response = "الرقم غير صحيح! أعد كتابة رقم مصري مكون من 11 رقماً."

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
