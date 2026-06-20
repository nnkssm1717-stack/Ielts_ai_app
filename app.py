import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from PIL import Image
import datetime

# 1. ページ設定（一番最初に書く）
st.title("IELTS Writing AI添削")

# 2. 設定の読み込み（エラーを防ぐため関数化などせずシンプルに記述）
if "gcp_service_account" in st.secrets and "GOOGLE_API_KEY" in st.secrets:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    SHEET_ID = "1clFXA6yF_I2IKPx2Kf8ppGDWIlIYar8xfiVDLciTKqE"
    sheet = client.open_by_key(SHEET_ID).sheet1

    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secretsの設定が読み込めていません。")
    st.stop()

# 3. UIと問題生成
st.header("💡 練習問題を作る")
if st.button("ランダムに問題を作成する"):
    with st.spinner('問題を作成中...'):
        topic_prompt = "IELTS Writing Task 2の練習問題を1つ生成して。アカデミックなトピックでお願いします。"
        problem = model.generate_content(topic_prompt)
        st.session_state.problem_text = problem.text

if "problem_text" in st.session_state:
    st.info(f"### 本日のお題:\n{st.session_state.problem_text}")

st.divider()

user_name = st.text_input("ユーザー名を入力")
style_input = st.text_input("使いたい文法やスラング、理想のスタイルを入力 (任意)")
text_input = st.text_area("直接英文を入力して添削もできます")
uploaded_file = st.file_uploader("手書きのノート写真をアップロード", type=["jpg", "png"])

# 4. 添削処理
if st.button("添削開始"):
    if uploaded_file is None and not text_input:
        st.warning("写真か英文のどちらかを入力してください！")
    else:
        with st.spinner('添削中...'):
            prompt_normal = "このIELTSのライティングを添削して。Bandスコアと改善点を表示して。"
            prompt_style = f"この英文を、以下のこだわり・スラングを反映させて添削して。こだわり: {style_input}。Bandスコアと改善点を表示して。"
            
            # 添削実行
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                res1 = model.generate_content([prompt_normal, image])
                res2 = model.generate_content([prompt_style, image])
            else:
                res1 = model.generate_content([prompt_normal, text_input])
                res2 = model.generate_content([prompt_style, text_input])
            
            st.subheader("【通常のIELTS添削】")
            st.write(res1.text)
            st.subheader("【こだわり反映版】")
            st.write(res2.text)
            
            # 保存
            input_content = "写真データ" if uploaded_file else text_input
            log_data = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user_name, "Writing", input_content, res1.text, "完了"]
            sheet.append_row(log_data)
            st.success("スプレッドシートに保存しました！")
