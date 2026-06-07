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
        msg = f"🎯 عميل حقيقي جديد!\nالاسم: {name}\nالرقم: {phone}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        requests.get(url, params=params)
        return True
    except: return False

st.title("🎯 بوت المبيعات الذكي (مطور)")

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    if "CAPTURE_DATA:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("تفضل، أنا معك..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        
        # تعليمات البوت مع التمييز بين الأسماء
        system_prompt = """أنت خبير مبيعات. مهمتك استخراج الاسم ورقم الهاتف.
        - إذا كان الاسم المذكور قصيراً أو يحتمل التشابه، اطلب من العميل كتابة الاسم بالكامل (الاسم واسم العائلة).
        - اكتب فقط في نهاية ردك: CAPTURE_DATA: [الاسم بالكامل] | [الرقم]
        - تأكد أن الرقم مصري (010, 011, 012, 015) وبطول 11 رقم."""
        
        conversation = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", messages=conversation, temperature=0
        ).choices[0].message.content
        
        if "CAPTURE_DATA:" in response:
            try:
                extracted = response.split("CAPTURE_DATA:")[1].strip()
                name, phone = [x.strip() for x in extracted.split("|")]
                
                # --- نظام الفلترة الذكي ---
                phone_clean = re.sub(r'\D', '', phone)
                valid_prefixes = ('010', '011', '012', '015')
                
                # التحقق من أن الرقم 11 رقم ويبدأ بالأكواد الصحيحة
                is_valid_phone = len(phone_clean) == 11 and phone_clean.startswith(valid_prefixes)
                
                # التحقق من الاسم (يجب أن يحتوي على مسافة واحدة على الأقل لضمان وجود اسم ولقب)
                is_valid_name = len(name.split()) >= 2 and not re.search(r'[!@#$%^&*()_+]', name)
                
                if is_valid_phone and is_valid_name:
                    if send_telegram_alert(name, phone_clean):
                        st.toast(f"✅ تم تأكيد بيانات العميل: {name}")
                    else:
                        st.toast("⚠️ فشل الاتصال بتليجرام")
                else:
                    st.toast(f"❌ بيانات مرفوضة: الاسم يجب أن يكون رباعياً أو اسمين على الأقل، والرقم مصري 11 رقم.")
            
            except Exception as e:
                st.toast("⚠️ خطأ في تنسيق البيانات")
            
            response = response.split("CAPTURE_DATA:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
