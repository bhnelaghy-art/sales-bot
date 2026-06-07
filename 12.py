import streamlit as st
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

# إعدادات الـ Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
GCP_CREDENTIALS = json.loads(st.secrets["GCP_CREDENTIALS"])

def append_to_sheet(name, phone):
    try:
        # إعداد الاتصال بجوجل شيت
        creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = build("sheets", "v4", credentials=creds)
        
        # تجهيز البيانات
        values = [[name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
        
        # إضافة البيانات للنطاق المباشر (بدون الاعتماد على اسم الورقة)
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="A:C", 
            valueInputOption="RAW",
            body={"values": values}
        ).execute()
        
        return True
    except Exception as e:
        return str(e)

st.title("🎯 اختبار تسجيل البيانات")

name = st.text_input("الاسم")
phone = st.text_input("رقم الهاتف")

if st.button("تجربة التسجيل في الشيت"):
    if name and phone:
        result = append_to_sheet(name, phone)
        if result == True:
            st.success("✅ تم التسجيل بنجاح في الشيت!")
        else:
            st.error(f"خطأ: {result}")
    else:
        st.warning("يرجى إدخال الاسم والرقم أولاً.")
