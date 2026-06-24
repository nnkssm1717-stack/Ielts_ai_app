import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
import random
import datetime
import time
import gspread
from google.oauth2.service_account import Credentials
from google.api_core import exceptions as gexc

# ============================================================
# セキュリティチェック：Secretsの有無を確認
# ============================================================
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("エラー: Secretsに 'GOOGLE_API_KEY' が設定されていません。Manage app > Settings > Secrets で設定してください。")
    st.stop()

# API設定
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


# ============================================================
# モデル設定（無料枠のめやす・おすすめ）
# ============================================================
# 無料枠の数値は変動するため、ここはあくまで参考値。正確な上限はアカウント/時期で
# 変わるので AI Studio (https://aistudio.google.com/rate-limit) で確認すること。
RATE_LIMIT_NOTE_DATE = "2026年6月時点の参考値"

# キーは Gemini のモデルID。表示はこの並び順（上ほど新しさ・推奨度が高い）。
MODEL_CATALOG = {
    "gemini-3-flash": {
        "label": "Gemini 3 Flash",
        "free": "約10 RPM / 25万 TPM / 1,500 RPD",
        "note": "新しめで精度と無料枠のバランスが良い。",
        "recommended": True,
    },
    "gemini-2.5-flash": {
        "label": "Gemini 2.5 Flash",
        "free": "約5 RPM（環境による）",
        "note": "高精度だが1分あたりの無料枠が小さめ。",
        "recommended": False,
    },
    "gemini-2.5-flash-lite": {
        "label": "Gemini 2.5 Flash-Lite",
        "free": "RPM多め / 精度は軽め",
        "note": "とにかく回数を稼ぎたいとき向き。",
        "recommended": False,
    },
}


@st.cache_resource
def get_model(model_name):
    return genai.GenerativeModel(model_name)


@st.cache_data(ttl=3600)
def list_available_models():
    """generateContent対応モデル名（'models/'接頭辞なし）の一覧。取得失敗時は空リスト。"""
    try:
        return [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
    except Exception:
        return []


def _retry_seconds(e, default=25):
    """例外に retry_delay があればその秒数、無ければ既定値を返す。"""
    rd = getattr(e, "retry_delay", None)
    if rd is not None and getattr(rd, "seconds", 0):
        return rd.seconds + 1
    return default


def generate_with_retry(model, contents, max_retries=1):
    """429（無料枠のレート上限）に当たったら、サーバー指定の待機後に一度だけ再試行する。

    1分あたりの上限に対しては、リトライ回数を増やすほど同じ60秒窓で
    リクエストを消費して逆効果になるため、再試行は1回だけにしている。
    """
    for attempt in range(max_retries + 1):
        try:
            return model.generate_content(contents)
        except gexc.ResourceExhausted as e:
            if attempt >= max_retries:
                raise
            wait = _retry_seconds(e)
            st.warning(
                f"無料枠の上限（1分あたりのリクエスト数）に達しました。"
                f"{wait}秒待って一度だけ自動で再試行します…"
            )
            time.sleep(wait)


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
    creds = Credentials.from_service_account_info(dict(
        st.secrets), scopes=scopes
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
# Task 1 と Task 2 のリストを分ける
TASK1_QUESTIONS = [
    "Task 1: The bar chart shows the spending on five categories in 2025. Summarize.",
    "Task 1: The table compares the number of students in three courses 2020-2025.",
    "Task 1: The line graph shows changes in oil production from 1990 to 2010.",
    "Task 1: The pie chart shows the reasons for choosing to move to a new city.",
    "Task 1: The diagram illustrates the process of making recycled paper.",
    "Task 1: The map shows the changes in a village center between 1995 and 2015.",
    "Task 1: The bar chart shows the number of visitors to different museums.",
    "Task 1: The table indicates the main causes of land degradation worldwide.",
    "Task 1: The graph shows the employment rates in three different sectors.",
    "Task 1: The chart shows the energy consumption in different types of households."
]
TASK2_QUESTIONS = [
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
    # タスクタイプをランダムに決定
    st.session_state.task_type = random.choice(["Task 1", "Task 2"])
    
    # 決定したタスクに応じて問題を抽出
    if st.session_state.task_type == "Task 1":
        st.session_state.prob = random.choice(TASK1_QUESTIONS)
    else:
        st.session_state.prob = random.choice(TASK2_QUESTIONS)

if "prob" in st.session_state:
    st.info(f"### お題 ({st.session_state.task_type}):\n{st.session_state.prob}")
    if st.session_state.task_type == "Task 1":
        st.warning("⚠️ Task 1です。グラフや表の画像（またはデータ詳細）を参考にしてください。")

# --- サイドバー：モデル選択 ---
st.sidebar.header("⚙️ モデル設定")

available = list_available_models()
# 表示候補：カタログ順で実在するもの → カタログ外の実在モデル
preferred = [m for m in MODEL_CATALOG if (not available) or (m in available)]
others = [m for m in available if m not in MODEL_CATALOG]
options = preferred + others
if not options:
    options = list(MODEL_CATALOG.keys())

# 現在のおすすめ：実在する中で recommended=True の最上位、無ければ先頭
recommended_id = next(
    (m for m in options if MODEL_CATALOG.get(m, {}).get("recommended")),
    options[0],
)


def _model_label(model_id):
    return MODEL_CATALOG.get(model_id, {}).get("label", model_id)


def _fmt(model_id):
    label = _model_label(model_id)
    return f"{label} ⭐おすすめ" if model_id == recommended_id else label


selected_model = st.sidebar.selectbox(
    "使用モデル", options, index=options.index(recommended_id), format_func=_fmt
)

# このAPIキーで使えるモデル数（list_models の結果から判定）
if available:
    st.sidebar.caption(f"🔑 このキーで使えるモデル: {len(available)} 種類")
else:
    st.sidebar.caption("🔑 モデル一覧を取得できませんでした（APIキーを確認してください）")

# 選択中モデルの情報
info = MODEL_CATALOG.get(selected_model)
if info:
    st.sidebar.caption(f"📊 無料枠の目安：{info['free']}")
    st.sidebar.caption(info["note"])
else:
    st.sidebar.caption("このモデルの無料枠情報は未登録です。AI Studio で確認してください。")

st.sidebar.success(f"⭐ 現在のおすすめ：{_model_label(recommended_id)}")

with st.sidebar.expander("モデル別 無料枠のめやす"):
    rows = ["| モデル | 無料枠の目安 |", "|---|---|"]
    for m in options:
        meta = MODEL_CATALOG.get(m)
        if meta:
            star = "⭐ " if m == recommended_id else ""
            rows.append(f"| {star}{meta['label']} | {meta['free']} |")
    st.markdown("\n".join(rows))
    st.caption(f"※{RATE_LIMIT_NOTE_DATE}。実際の上限は時期・アカウントで変動します。")
    st.markdown("[AI Studio で自分の上限を確認](https://aistudio.google.com/rate-limit)")

model = get_model(selected_model)

# --- 設定項目 ---
# ラベルの行数差（右は折り返して2行）で入力欄がずれないよう、ラベル高さを揃える
LABEL_STYLE = "min-height:3em; display:flex; align-items:flex-end; font-size:0.875rem; margin-bottom:0.25rem;"

# タスクタイプが未選択ならデフォルトはTask 2にする
task_type = st.session_state.get("task_type", "Task 2")
target_words = 150 if task_type == "Task 1" else 250

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"<div style='{LABEL_STYLE}'>目標Bandスコア</div>", unsafe_allow_html=True)
    target_score = st.selectbox(
        "目標Bandスコア", ["5.5", "6.0", "6.5", "7.0", "7.5", "8.0"],
        label_visibility="collapsed",
    )
with col2:
    st.markdown(
        f"<div style='{LABEL_STYLE}'>理想のスタイル（例：スラング、カジュアル、フォーマル、論理的、アカデミック）</div>",
        unsafe_allow_html=True,
    )
    style_input = st.text_input("理想のスタイル", label_visibility="collapsed")

TARGET_WORDS = 250  # IELTS Writing Task 2 の目安語数
# (既存のラベル等のコードはそのまま)
st.caption(f"現在のタスク: {task_type} （目安: {target_words}語以上）") # これを追加

text_input = st.text_area("英文を入力", height=200)

# --- 単語数カウント（入力中＝1キーごとに更新） ---
# Streamlit標準の text_area は「フォーカスが外れた時」しか値を確定しないため、
# ブラウザ側のJSで本物の入力欄(textarea)の input イベントを直接監視して更新する。
components.html(
    f"""
    <div id="wc-box" style="font-family: 'Source Sans Pro', sans-serif; color:#555;">
      <div id="wc-text" style="font-size:0.85rem; margin-bottom:4px;">📝 単語数: 0 / {TARGET_WORDS}</div>
      <div style="background:#e6e9ef; border-radius:6px; height:8px; width:100%; overflow:hidden;">
        <div id="wc-bar" style="background:#4c8bf5; height:8px; width:0%; transition:width .1s;"></div>
      </div>
    </div>
    <script>
      const TARGET = {TARGET_WORDS};
      function findTextarea() {{
        try {{
          return window.parent.document.querySelector('textarea[aria-label="英文を入力"]');
        }} catch (e) {{ return null; }}
      }}
      function update() {{
        const txt = document.getElementById('wc-text');
        const bar = document.getElementById('wc-bar');
        const ta = findTextarea();
        if (!ta) {{ txt.textContent = '（単語数を表示できませんでした）'; return; }}
        const v = ta.value.trim();
        const n = v === '' ? 0 : v.split(/\\s+/).length;
        bar.style.width = Math.min(n / TARGET * 100, 100) + '%';
        bar.style.background = n >= TARGET ? '#2ecc71' : '#4c8bf5';
        if (n === 0) txt.textContent = '📝 単語数: 0 / ' + TARGET;
        else if (n < TARGET) txt.textContent = '📝 単語数: ' + n + ' / ' + TARGET + '（あと ' + (TARGET - n) + ' 語）';
        else txt.textContent = '📝 単語数: ' + n + ' / ' + TARGET + ' ✅ 目安に到達';
      }}
      const ta = findTextarea();
      if (ta) {{ ta.addEventListener('input', update); ta.addEventListener('keyup', update); }}
      update();
      setInterval(update, 400);  // 貼り付け・IME・再描画への保険
    </script>
    """,
    height=55,
)

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
            お題（設問）: {task_type}
            【目標語数】: {target_words}語以上
            目標スコア: {target_score}
            ユーザーの希望スタイル: {style_input}

            以下の形式で回答してください：
            1. **現在の推定Bandスコア**
            2. **詳細な添削結果** (元の文章と比較してください)
            3. **目標スコアに到達するための具体的な改善ポイント**
            4. **目標スコア基準での添削書き換え例**
            5. **語数チェック（目標の{target_words}語に達しているか）**
            """
            try:
                if uploaded_file:
                    res = generate_with_retry(model, [prompt, Image.open(uploaded_file)])
                else:
                    res = generate_with_retry(model, [prompt, text_input])
                st.markdown("---")
                st.write(res.text)

                # --- スプレッドシートへ保存 ---
                user_input = text_input if text_input else f"（画像アップロード: {uploaded_file.name}）"
                ok, err = save_to_sheet(task_type, question, target_score, style_input, user_input, res.text)
                if ok:
                    st.success("スプレッドシートに保存しました。")
                else:
                    st.warning(f"添削は完了しましたが、スプレッドシート保存に失敗しました: {err}")

            except gexc.ResourceExhausted:
                st.error(
                    "無料枠のレート上限（1分あたりのリクエスト数）に達しました。"
                    "1分ほど待ってから、もう一度「添削開始」を押してください。"
                )
            except Exception as e:
                st.error(f"エラー: {e}")
