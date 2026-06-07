import streamlit as st
import requests
import re
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- إضافة لوحة التحكم الإدارية ---
with st.sidebar:
    st.header("⚙️ لوحة تحكم المدير")
    password = st.text_input("كلمة مرور المدير:", type="password")
    
    if password == "1234":  # يمكنك تغيير كلمة المرور هنا
        st.success("أهلاً بك يا مدير!")
        names, phones = get_existing_data()
        st.metric("إجمالي العملاء", len(names))
        
        if st.button("عرض آخر 5 سجلات"):
            try:
                creds = Credentials.from_service_account_info(GCP_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
                service = build("sheets", "v4", credentials=creds)
                sheet_name = get_sheet_name(service)
                result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:C").execute()
                rows = result.get('values', [])
                if rows:
                    st.table(rows[-5:])
                else:
                    st.write("لا توجد بيانات بعد.")
            except Exception as e:
                st.error(f"خطأ في جلب البيانات: {e}")
    else:
        st.warning("أدخل كلمة المرور لعرض الإحصائيات")

st.title("🎯 نظام تسجيل العملاء (الربط التلقائي)")

# ... باقي الكود الخاص بك يبدأ من هنا (if "step" not in st.session_state...)
