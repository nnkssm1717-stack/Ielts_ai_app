import streamlit as st
from openai import OpenAI
from PIL import Image
import random
import base64
import io

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 画像をBase64形式に変換（OpenAI APIで画像を送るための形式）
def get_image_base64(uploaded_file):
    image = Image.open(uploaded_file)
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# 問題リスト
IELTS_QUESTIONS = ["Some people think that the best way to reduce crime is to give longer prison sentences. Discuss both views.", "Nowadays, many people work from home. What are the advantages and disadvantages?"]

st.title("IELTS Writing AI添削 (OpenAI版)")

if st.button("ランダムに問題を出題"):
    st.session_state.problem_text = random.choice(IELTS_QUESTIONS)

if "problem_text" in st.session_state:
    st.info(f"### お題:\n{st.session_state.problem_text}")

# 入力項目
style_input = st.text_input("使いたい文法やスラング、理想のスタイルを入力 (任意)")
text_input = st.text_area("直接英文を入力して添削")
uploaded_file = st.file_uploader("ノート写真をアップロード", type=["jpg", "png"])

if st.button("添削開始"):
    if not text_input and not uploaded_file:
        st.warning("内容を入力してください。")
    else:
        with st.spinner('添削中...'):
            try:
                # プロンプトの構築
                prompt = f"IELTSのライティングを添削し、Bandスコアと改善点を教えてください。ユーザーの希望スタイル: {style_input}"
                
                messages = [{"role": "system", "content": "あなたはIELTSの試験官です。"}]
                
                # 画像がある場合とない場合でメッセージを分岐
                if uploaded_file:
                    base64_image = get_image_base64(uploaded_file)
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    })
                else:
                    messages.append({"role": "user", "content": f"{prompt}\n\n英文: {text_input}"})

                # API呼び出し
                response = client.chat.completions.create(
                    model="gpt-4o", # 画像認識に対応したモデル
                    messages=messages
                )
                st.write(response.choices[0].message.content)
                st.success("添削完了！")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
            except Exception as e:
                st.error(f"エラー: {e}")
