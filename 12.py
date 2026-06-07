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

st.title("🎯 بوت المبيعات (نظام الفلترة الذكي)")

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    if "CAPTURE_DATA:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("تفضل، أنا معك..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        
        system_prompt = """أنت خبير مبيعات. مهمتك استخراج الاسم ورقم الهاتف من كلام العميل.
        اكتب فقط في نهاية ردك: CAPTURE_DATA: [الاسم] | [الرقم]
        - إذا كان الاسم يبدو وهمياً (مثلاً: حروف عشوائية، أو رموز)، لا ترسل الكود.
        - تأكد أن الرقم المكتوب هو رقم هاتف مصري صحيح."""
        
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
                # 1. تنظيف الرقم من أي مسافات
                phone_clean = re.sub(r'\D', '', phone)
                
                # 2. التحقق من الرقم (11 رقم ويبدأ بـ 01)
                is_valid_phone = len(phone_clean) == 11 and phone_clean.startswith('01')
                
                # 3. التحقق من الاسم (أكثر من 3 حروف ولا يحتوي على رموز غريبة)
                is_valid_name = len(name) > 3 and not re.search(r'[!@#$%^&*()_+]', name)
                
                if is_valid_phone and is_valid_name:
                    if send_telegram_alert(name, phone_clean):
                        st.toast(f"✅ تم تأكيد العميل: {name}")
                    else:
                        st.toast("⚠️ خطأ في الاتصال بتليجرام")
                else:
                    st.toast(f"❌ تم رفض بيانات وهمية: الاسم {name} أو الرقم {phone}")
            
            except Exception as e:
                st.toast("⚠️ بيانات غير مكتملة")
            
            response = response.split("CAPTURE_DATA:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
