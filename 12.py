import streamlit as st
import requests

# إعدادات الـ Secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

def send_test_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.get(url, params=params)
        return response.status_code == 200
    except Exception as e:
        return str(e)

st.title("🎯 اختبار تليجرام")

test_msg = st.text_input("اكتب رسالة للتجربة:")

if st.button("إرسال رسالة لتليجرام"):
    if test_msg:
        result = send_test_telegram(test_msg)
        if result == True:
            st.success("✅ وصلت الرسالة على تليجرام!")
        else:
            st.error(f"خطأ: {result}")
    else:
        st.warning("اكتب رسالة الأول!")
