import streamlit as st
import json
from groq import Groq

# إعدادات الـ Secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("خطأ: مفتاح Groq غير موجود في الـ Secrets")
    st.stop()

st.title("🎯 منظومة المبيعات الذكية")

# معالجة الرسائل
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("اكتب رسالتك هنا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            temperature=0.1
        )
        response = completion.choices[0].message.content
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
