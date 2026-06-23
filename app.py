import streamlit as st
import google.generativeai as genai
from PIL import Image
import random

# セキュリティチェック：Secretsの有無を確認
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("エラー: Secretsに 'GOOGLE_API_KEY' が設定されていません。Manage app > Settings > Secrets で設定してください。")
    st.stop()

# API設定
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-2.5-flash')

model = get_model()

# 20問の問題リスト
QUESTIONS = [
    "Some people think that the best way to reduce crime is to give longer prison sentences. Discuss both views.",
    "Nowadays, many people work from home. What are the advantages and disadvantages?",
    "Global warming is a serious issue. What measures should governments take?",
    "Should schools teach students how to manage their money? Give reasons.",
    "Is it better to grow up in the city or the countryside?",
    "Does the news media have too much influence on people's opinions?",
    "Should governments ban dangerous sports? To what extent do you agree?",
    "Is it important for students to study history? Give reasons.",
    "Should everyone be a vegetarian? Do you agree or disagree?",
    "Traffic problems are increasing. What solutions can you suggest?",
    "Should public transport be free? Give your reasons.",
    "Should university education be free? To what extent do you agree?",
    "Advertising influences our choices. Is this positive or negative?",
    "Should elderly people be cared for by families or the state?",
    "Living in small apartments: How does this affect people's lives?",
    "Is it important to learn about other cultures?",
    "Do sports stars earn too much money? Do you agree or disagree?",
    "Buildings should be useful, not beautiful. Do you agree or disagree?",
    "Has technology improved our lives or made them complicated?",
    "Should parents teach children to be good members of society?"
]

st.title("IELTS Writing AI添削")

if st.button("ランダムに問題を出題"):
    st.session_state.prob = random.choice(QUESTIONS)

if "prob" in st.session_state:
    st.info(f"### お題:\n{st.session_state.prob}")

style = st.text_input("目指すスタイル（文法・スラング等）")
text = st.text_area("英文を入力")
file = st.file_uploader("写真をアップロード", type=["jpg", "png"])

if st.button("添削開始"):
    if not text and not file:
        st.warning("入力してください。")
    else:
        with st.spinner('添削中...'):
            try:
                p = f"IELTSの試験官として、この英文を添削し、Bandスコアと改善点を教えて。スタイル: {style}"
                if file:
                    res = model.generate_content([p, Image.open(file)])
                else:
                    res = model.generate_content([p, text])
                st.write(res.text)
            except Exception as e:
                st.error(f"APIエラー: {e}")
