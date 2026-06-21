import streamlit as st
import google.generativeai as genai
from PIL import Image
import random

# IELTS Writing 問題リスト（20問に整理）
IELTS_QUESTIONS = [
    "Some people think that the best way to reduce crime is to give longer prison sentences. Discuss both views.",
    "Nowadays, many people work from home. What are the advantages and disadvantages of this trend?",
    "Global warming is one of the most serious issues. What measures should governments take to solve this?",
    "Should schools teach students how to manage their money? Give reasons.",
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
    "Some people believe that parents should teach children how to be good members of society. Do you agree?"
]

# AI設定：関数は1つ、returnも関数内に正しく配置
@st.cache_resource
def get_ai_model():
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # 確実に存在するモデル名を使用
    return genai.GenerativeModel('gemini-1.0-pro')

model = get_ai_model()

# UI表示
st.title("IELTS Writing AI添削")

if st.button("ランダムに問題を出題"):
    st.session_state.problem_text = random.choice(IELTS_QUESTIONS)

if "problem_text" in st.session_state:
    st.info(f"### 本日のお題:\n{st.session_state.problem_text}")

# 入力欄
user_name = st.text_input("ユーザー名を入力")
style_input = st.text_input("目指すスタイル（文法・スラング等）を入力")
text_input = st.text_area("直接英文を入力して添削")
uploaded_file = st.file_uploader("ノート写真をアップロード", type=["jpg", "png"])

if st.button("添削開始"):
    if not text_input and not uploaded_file:
        st.warning("英文を入力するか、写真をアップロードしてください。")
    else:
        with st.spinner('添削中...'):
            prompt = f"IELTSのライティングを添削し、Bandスコアと改善点を教えて。希望スタイル: {style_input}"
            try:
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    res = model.generate_content([prompt, image])
                else:
                    res = model.generate_content([prompt, text_input])
                st.write(res.text)
                st.success("添削完了！")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
