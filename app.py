import streamlit as st
from openai import OpenAI
from PIL import Image
import random

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("IELTS Writing AI添削 (OpenAI版)")

# (問題リストは前回のものをそのまま使えます)
IELTS_QUESTIONS = ["Some people think that the best way to reduce crime is to give longer prison sentences. Discuss both views.", "Nowadays, many people work from home. What are the advantages and disadvantages?"]

if st.button("ランダムに問題を出題"):
    st.session_state.problem_text = random.choice(IELTS_QUESTIONS)

if "problem_text" in st.session_state:
    st.info(f"### お題:\n{st.session_state.problem_text}")

text_input = st.text_area("英文をここに入力")

if st.button("添削開始"):
    if not text_input:
        st.warning("内容を入力してください。")
    else:
        with st.spinner('添削中...'):
            try:
                # OpenAIのAPI呼び出し
                response = client.chat.completions.create(
                    model="gpt-4o-mini", # 安価で高性能なモデルを指定
                    messages=[
                        {"role": "system", "content": "あなたはIELTSの試験官です。英文を添削し、Bandスコアと改善点を提示してください。"},
                        {"role": "user", "content": text_input}
                    ]
                )
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(f"エラー: {e}")
