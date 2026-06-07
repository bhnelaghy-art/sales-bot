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
        return True
    except: 
        return False

# واجهة الشات
st.title("🎯 بوت المبيعات الذكي (وضع التشخيص)")

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    if "CAPTURE_DATA:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        
        # تعليمات آمرة ومحددة جداً
        system_prompt = """أنت مساعد مبيعات. بمجرد حصولك على اسم العميل ورقم هاتفه، يجب أن تضيف في نهاية ردك هذا السطر فقط:
        CAPTURE_DATA: الاسم | الرقم
        مثال: CAPTURE_DATA: محمد أحمد | 01012345678
        لا تكتب أي شيء آخر بجانب هذه الصيغة."""
        
        conversation = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=conversation, 
            temperature=0.1
        ).choices[0].message.content
        
        # معالجة البيانات مع تشخيص الأخطاء
        if "CAPTURE_DATA:" in response:
            try:
                raw_data = response.split("CAPTURE_DATA:")[1].strip()
                # إظهار ما التقطه البوت (للتشخيص)
                st.toast(f"تم التقاط: {raw_data}")
                
                name, phone = raw_data.split("|")
                
                if len(name.strip()) > 0 and len(phone.strip()) > 3:
                    if send_telegram_alert(name.strip(), phone.strip()):
                        st.toast("✅ تم إرسال البيانات لتليجرام!")
                    else:
                        st.error("خطأ: فشل الاتصال بتليجرام")
                else:
                    st.error(f"خطأ: البيانات غير كافية (الاسم: {name}, الرقم: {phone})")
            except Exception as e:
                st.error(f"خطأ في صيغة البيانات: {str(e)}")
            
            # تنظيف رد البوت للعرض
            response = response.split("CAPTURE_DATA:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
