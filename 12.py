import streamlit as st
import requests
import re

# إعدادات الـ Secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# تخزين الأسماء والأرقام للتأكد من عدم التكرار مطلقاً
if "registered_names" not in st.session_state:
    st.session_state.registered_names = []
if "registered_phones" not in st.session_state:
    st.session_state.registered_phones = []

# دالة إرسال التنبيه
def send_telegram_alert(name, phone):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🎯 عميل جديد!\nالاسم: {name}\nالرقم: {phone}"}
        requests.get(url, params=params)
        return True
    except: return False

st.title("🎯 نظام تسجيل العملاء (صارم جداً)")

if "step" not in st.session_state: st.session_state.step = "ask_name"
if "temp_name" not in st.session_state: st.session_state.temp_name = ""
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("أدخل البيانات..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        response = ""
        
        if st.session_state.step == "ask_name":
            clean_name = user_input.strip().lower()
            
            # شرط 1: التأكد من أنه اسم ثلاثي
            if len(user_input.split()) < 3:
                response = "عذراً، يرجى إدخال الاسم الثلاثي بالكامل."
            
            # شرط 2: التأكد من عدم تكرار الاسم في قاعدة بياناتنا
            elif clean_name in st.session_state.registered_names:
                response = "هذا الاسم مسجل لدينا مسبقاً، لا يمكن تسجيله مرة أخرى."
            
            else:
                st.session_state.temp_name = user_input.strip()
                st.session_state.step = "ask_phone"
                response = "تم حفظ الاسم. من فضلك الآن أرسل رقم الهاتف (11 رقم)."

        elif st.session_state.step == "ask_phone":
            phone_clean = re.sub(r'\D', '', user_input)
            
            # شرط 1: التأكد من صحة الرقم
            if len(phone_clean) != 11 or not phone_clean.startswith(('010', '011', '012', '015')):
                response = "الرقم غير صحيح! أعد كتابة رقم مصري مكون من 11 رقماً."
            
            # شرط 2: التأكد من عدم تكرار الرقم
            elif phone_clean in st.session_state.registered_phones:
                response = "هذا الرقم مسجل مسبقاً في نظامنا."
                st.session_state.step = "ask_name" # العودة للبداية
            
            else:
                if send_telegram_alert(st.session_state.temp_name, phone_clean):
                    st.session_state.registered_names.append(st.session_state.temp_name.lower())
                    st.session_state.registered_phones.append(phone_clean)
                    response = "✅ تم التسجيل بنجاح!"
                else:
                    response = "خطأ في الاتصال، حاول لاحقاً."
                st.session_state.step = "ask_name"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
