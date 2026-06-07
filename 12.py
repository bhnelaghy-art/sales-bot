import streamlit as st
import requests
from groq import Groq

# إعدادات الـ Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# دالة إرسال التنبيه
def send_telegram_alert(name, phone):
    try:
        msg = f"🎯 بيانات عميل مؤكدة!\nالاسم: {name}\nالرقم: {phone}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        requests.get(url, params=params)
        return True
    except: return False

st.title("🎯 بوت المبيعات - وضع الذكاء المتطور")

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    if "CAPTURE_DATA:" not in msg["content"]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("تفضل، أنا معك..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        
        # التحديث هنا: "تفكير منطقي" للبوت
        system_prompt = """أنت خبير مبيعات تحليلي. 
        1. ابدأ بتحليل كلام العميل: هل ذكر اسماً ورقم هاتف؟
        2. إذا نعم، قم بتنظيف البيانات (إزالة أي رموز زائدة).
        3. اكتب في نهاية ردك حصراً: CAPTURE_DATA: [الاسم] | [الرقم]
        4. إذا كانت البيانات ناقصة، لا تكتب أي شيء ولا ترسل أي كود."""
        
        conversation = [{"role": "system", "content": system_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=conversation, 
            temperature=0
        ).choices[0].message.content
        
        # معالجة متطورة مع نظام مراقبة
        if "CAPTURE_DATA:" in response:
            try:
                # استخراج البيانات بدقة
                extracted = response.split("CAPTURE_DATA:")[1].strip()
                name, phone = [x.strip() for x in extracted.split("|")]
                
                # إظهار المراقبة في الـ Toast
                st.toast(f"🔎 المراقبة: تم اكتشاف بيانات (الاسم: {name} | الرقم: {phone})")
                
                if len(name) > 1 and len(phone) >= 7:
                    if send_telegram_alert(name, phone):
                        st.toast("✅ تم إرسال البيانات لتليجرام بنجاح!")
                    else:
                        st.toast("⚠️ فشل في إرسال التليجرام!")
                else:
                    st.toast("❌ بيانات غير مكتملة، لم يتم الإرسال.")
            except Exception as e:
                st.toast(f"⚠️ خطأ في تحليل البيانات: {e}")
            
            response = response.split("CAPTURE_DATA:")[0]
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
