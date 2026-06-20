import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from PIL import Image
import datetime
import random # ランダム選択のために追加

# 1. 問題リスト（ここを増やせば増やすほど問題が増えます）
IELTS_QUESTIONS = [
    "Some people think that the best way to reduce crime is to give longer prison sentences. Discuss both views and give your opinion.",
    "Nowadays, many people work from home. What are the advantages and disadvantages of this trend?",
    "Should schools teach students how to manage their money? Give reasons for your answer.",
    "Global warming is one of the most serious issues. What measures should governments take to solve this?",
    # ...ここに20個ほど追加してください...
]

# 2. AIの設定
@st.cache_resource
def get_ai_model():
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_ai_model()

# 3. アプリの見た目
st.title("IELTS Writing AI添削")

# 【改善】問題選択機能（APIを使わないので一瞬で表示されます）
st.header("💡 練習問題を作る")
if st.button("ランダムに問題を出題"):
    # リストから1つ選ぶ
    st.session_state.problem_text = random.choice(IELTS_QUESTIONS)

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
