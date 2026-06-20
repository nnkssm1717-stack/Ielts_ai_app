st.write("読み込めたSecretsのキー一覧:")
st.write(list(st.secrets.keys()))
st.stop() 
import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from PIL import Image
import datetime

# 1. スプレッドシートの準備
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# JSONキーの中身を直接入力するか、Streamlitのsecretsを使って読み込みます
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
SHEET_ID = "1clFXA6yF_I2IKPx2Kf8ppGDWIlIYar8xfiVDLciTKqE"
sheet = client.open_by_key(SHEET_ID).sheet1

# 2. AIの設定 (Gemini)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. アプリの見た目
st.title("IELTS Writing AI添削")
user_name = st.text_input("ユーザー名を入力")
uploaded_file = st.file_uploader("手書きのノート写真をアップロード", type=["jpg", "png"])

if st.button("添削開始"):
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        # AIに写真を送って添削してもらう
        response = model.generate_content(["このIELTSのライティングを添削して。Band Scoreの目安と改善点を教えて。", image])
        
        # 結果を表示
        st.write(response.text)
        
        # スプレッドシートに保存
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sheet.append_row([date, user_name, "Writing", "写真データ", response.text, "分析中"])
        st.success("スプレッドシートに保存しました！")
