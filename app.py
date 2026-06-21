import streamlit as st
import google.generativeai as genai
from PIL import Image
import random

# APIキー設定（StreamlitのSecretsから読み込み）
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 20問のIELTSライティング問題リスト
IELTS_QUESTIONS = [
    "Some people think that the best way to reduce crime is to give longer prison sentences. Discuss both views.",
    "Nowadays, many people work from home. What are the advantages and disadvantages of this trend?",
    "Global warming is one of the most serious issues. What measures should governments take to solve this?",
    "Should schools teach students how to manage their money? Give reasons.",
    "Is it better for children to grow up in the city or in the countryside? Discuss.",
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
    "The main purpose of a building should be to be useful, not beautiful. Do you agree?",
    "Do you think that the development of technology has improved our lives?",
    "Some people believe that parents should teach children how to be good members of society. Do you agree?"
]

st.title("IELTS Writing AI添削")

# ランダム出題機能
if st.button("ランダムに問題を出題"):
    st.session_state.problem_text = random.choice(IELTS_QUESTIONS)

if "problem_text" in st.session_state:
    st.info(f"### 本日のお題:\n{st.session_state.problem_text}")

# 入力項目
style_input = st.text_input("目指すスタイル（文法・スラング等）を入力")
text_input = st.text_area("直接英文を入力")
uploaded_file = st.file_uploader("ノート写真をアップロード", type=["jpg", "png"])

# 添削処理
if st.button("添削開始"):
    if not text_input and not uploaded_file:
        st.warning("内容を入力するか、写真をアップロードしてください。")
    else:
        with st.spinner('AIが添削中です...'):
            try:
                prompt = f"あなたはIELTSの試験官です。以下の英文を添削し、Bandスコアと改善点を具体的に教えてください。希望スタイル: {style_input}"
                
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content([prompt, text_input])
                
                st.markdown("### 添削結果:")
                st.write(response.text)
                st.success("添削完了！")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
            except Exception as e:
                st.error(f"エラー: {e}")
