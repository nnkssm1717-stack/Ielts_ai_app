import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from PIL import Image
import datetime

# 1. スプレッドシートの準備
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
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
style_input = st.text_input("使いたい文法やスラング、理想のスタイルを入力 (任意)")
text_input = st.text_area("直接英文を入力して添削もできます")
uploaded_file = st.file_uploader("手書きのノート写真をアップロード", type=["jpg", "png"])

if st.button("添削開始"):
    prompt_normal = "このIELTSのライティングを添削して。Bandスコアと改善点を表示して。"
    prompt_style = f"この英文を、以下のこだわり・スラングを反映させて添削して。こだわり: {style_input}。Bandスコアと改善点を表示して。"
    
    response_text = ""
    log_data = []

    # 写真またはテキストがあるか確認
    if uploaded_file is not None or text_input:
        
        # 通常の添削
        st.subheader("【通常のIELTS添削】")
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            res1 = model.generate_content([prompt_normal, image])
            res2 = model.generate_content([prompt_style, image])
        else:
            res1 = model.generate_content([prompt_normal, text_input])
            res2 = model.generate_content([prompt_style, text_input])
        
        st.write(res1.text)
        
        # こだわり反映版
        st.subheader("【こだわり反映版】")
        st.write(res2.text)
        
        # スプレッドシート記録用
        input_content = "写真データ" if uploaded_file else text_input
        log_data = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user_name, "Writing", input_content, res1.text, "完了"]
        sheet.append_row(log_data)
        st.success("スプレッドシートに保存しました！")
        
    else:
        st.warning("写真か英文のどちらかを入力してください！")
