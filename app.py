import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from PIL import Image
import datetime
import random # ランダム選択のために追加

# 1. 問題リスト（ここを増やせば増やすほど問題が増えます）
# 1. 問題リスト（定番の30問に増やしました）
IELTS_QUESTIONS = [
    "Some people think that the best way to reduce crime is to give longer prison sentences. Discuss both views and give your opinion.",
    "Nowadays, many people work from home. What are the advantages and disadvantages of this trend?",
    "Global warming is one of the most serious issues. What measures should governments take to solve this?",
    "Should schools teach students how to manage their money? Give reasons for your answer.",
    "Some people think that it is best to work for the same organization for one's whole life. Do you agree or disagree?",
    "The use of mobile phones is becoming antisocial. To what extent do you agree or disagree?",
    "Many people think that art and music are not important in schools compared to science and technology. Do you agree?",
    "Some people believe that unpaid community service should be a compulsory part of high school programmes. To what extent do you agree?",
    "Tourism is causing environmental damage. What can be done to solve this problem?",
    "The gap between the rich and the poor is widening. What are the causes and solutions?",
    "Is it better for children to grow up in the city or in the countryside? Discuss the advantages of both.",
    "Do you think that the news media has too much influence on people's opinions?",
    "Some people think that governments should ban dangerous sports. To what extent do you agree?",
    "Is it important for students to study history? Give reasons for your answer.",
    "Some people believe that everyone should be a vegetarian. Do you agree or disagree?",
    "The increase in the number of cars is causing serious traffic problems. What solutions can you suggest?",
    "Do you think that public transport should be free of charge? Give your reasons.",
    "Some people think that university education should be free. To what extent do you agree?",
    "Advertising influences our choices. Is this a positive or negative development?",
    "Should elderly people be cared for by their families or by the state?",
    "Many people now have to live in small apartments. How does this affect people's lives?",
    "Is it important for people to learn about the culture of other countries?",
    "Some people think that sports stars earn too much money. Do you agree or disagree?",
    "The main purpose of a building should be to be useful, not beautiful. Do you agree or disagree?",
    "Do you think that the development of technology has improved our lives or made them more complicated?",
    "Some people believe that parents should teach children how to be good members of society. Do you agree?",
    "Many companies allow employees to use social media during work hours. Is this a good idea?",
    "Should the government spend more money on space exploration or on solving problems on Earth?",
    "Do you think that traditional festivals are becoming less important in modern society?",
    "Some people think that all university students should study a science subject. Do you agree or disagree?"
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
