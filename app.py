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
text_input = st.text_area("直接英文を入力して添削もできます")

uploaded_file = st.file_uploader("手書きのノート写真をアップロード", type=["jpg", "png"])

if st.button("添削開始"):
    response_text = ""
    
    # 1. 写真がアップロードされている場合
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        response = model.generate_content(["このIELTSのライティングを添削して。Bandスコアと改善点を表示して。", image])
        response_text = response.text
        log_data = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user_name, "Writing", "写真データ", response_text, "完了"]
    
    # 2. テキストが入力されている場合
    elif text_input:
        response = model.generate_content(["このIELTSのライティングを添削して。Bandスコアと改善点を表示して。", text_input])
        response_text = response.text
        log_data = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user_name, "Writing", text_input, response_text, "完了"]
    
    else:
        st.warning("写真か英文のどちらかを入力してください！")

    # 結果を表示して保存
    if response_text:
        st.write(response_text)
        sheet.append_row(log_data)
        st.success("スプレッドシートに保存しました！")
