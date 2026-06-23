import streamlit as st
import google.generativeai as genai
from PIL import Image
import random
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# セキュリティチェック：Secretsの有無を確認
# ============================================================
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("エラー: Secretsに 'GOOGLE_API_KEY' が設定されていません。Manage app > Settings > Secrets で設定してください。")
    st.stop()

# API設定
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-2.5-flash')


model = get_model()


# ============================================================
# Googleスプレッドシート接続
# ============================================================
HEADER = ["日時", "お題", "目標スコア", "スタイル", "入力内容", "添削結果"]


@st.cache_resource
def get_worksheet():
    """サービスアカウントで認証し、対象シートのworksheetを返す。"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    sh = client.open_by_url(st.secrets["spreadsheet_url"])
    ws = sh.sheet1

    # ヘッダー行が無ければ作成
    if not ws.acell("A1").value:
        ws.update("A1:F1", [HEADER])
    return ws


def save_to_sheet(question, target_score, style, user_input, result):
    """添削結果を1行追記する。成功なら(True, None)、失敗なら(False, エラー文字列)。"""
    try:
        ws = get_worksheet()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row(
            [now, question, target_score, style, user_input, result],
            value_input_option="USER_ENTERED",
        )
        return True, None
    except Exception as e:
        return False, str(e)


# ============================================================
# 問題リスト（20問）
# ============================================================
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
    "Should parents teach children to be good members of society?",
]

# ============================================================
# UI
# ============================================================
st.title("IELTS Writing AI添削")

if st.button("ランダムに問題を出題"):
    st.session_state.prob = random.choice(QUESTIONS)

if "prob" in st.session_state:
    st.info(f"### お題:\n{st.session_state.prob}")

# --- 設定項目 ---
col1, col2 = st.columns(2)
with col1:
    target_score = st.selectbox("目標Bandスコア", ["5.5", "6.0", "6.5", "7.0", "7.5", "8.0"])
with col2:
    style_input = st.text_input("理想のスタイル（例：フォーマル、論理的）")

text_input = st.text_area("英文を入力")
uploaded_file = st.file_uploader("写真をアップロード", type=["jpg", "png"])

if st.button("添削開始"):
    if not text_input and not uploaded_file:
        st.warning("内容を入力してください。")
    else:
        with st.spinner('AIが詳細分析中...'):
            question = st.session_state.get("prob", "（お題なし）")

            # 指示を具体化（ここがポイント）
            prompt = f"""
            あなたはIELTS専門の試験官です。以下の英文を添削してください。
            お題（設問）: {question}
            目標スコア: {target_score}
            ユーザーの希望スタイル: {style_input}

            以下の形式で回答してください：
            1. **現在の推定Bandスコア**
            2. **詳細な添削結果** (元の文章と比較してください)
            3. **目標スコアに到達するための具体的な改善ポイント**
            4. **目標スコア基準での添削書き換え例**
            """
            try:
                if uploaded_file:
                    res = model.generate_content([prompt, Image.open(uploaded_file)])
                else:
                    res = model.generate_content([prompt, text_input])
                st.markdown("---")
                st.write(res.text)

                # --- スプレッドシートへ保存 ---
                user_input = text_input if text_input else f"（画像アップロード: {uploaded_file.name}）"
                ok, err = save_to_sheet(question, target_score, style_input, user_input, res.text)
                if ok:
                    st.success("スプレッドシートに保存しました。")
                else:
                    st.warning(f"添削は完了しましたが、スプレッドシート保存に失敗しました: {err}")

            except Exception as e:
                st.error(f"エラー: {e}")
