import streamlit as st
import google.generativeai as genai

st.title("テスト")
key = st.secrets.get("GOOGLE_API_KEY")
st.write(f"APIキーは設定されていますか？: {'はい' if key else 'いいえ'}")

if key:
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content("こんにちは、テストです。")
        st.write("AIからの返答:", res.text)
    except Exception as e:
        st.write("エラー詳細:", e)
