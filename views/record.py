import streamlit as st
import sqlite3
from datetime import datetime

st.title("✍️ 수동 로그 기록")
st.markdown("---")
st.caption("위장/역류 증상(B-A-C)과 멘탈 지표를 기록합니다. (식단 및 UPF 횟수는 'AI 식단 관리' 페이지를 이용하세요)")

# ==========================================
# 📝 기록 폼 (Form)
# ==========================================
with st.form("daily_record_form"):
    st.markdown("### 🗓 날짜 선택")
    target_date = st.date_input("기록할 날짜", datetime.now())
    
    st.markdown("### 🚨 위장/역류 증상 (0~3점)")
    st.caption("0: 증상 없음 | 1: 약함 | 2: 중간 | 3: 심함")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        bloating_b = st.slider("🤢 더부룩함 (B)", 0, 3, 0)
    with col2:
        acid_a = st.slider("🔥 신물/쓰림 (A)", 0, 3, 0)
    with col3:
        cough_c = st.slider("🗣️ 잔기침 (C)", 0, 3, 0)

    st.divider()

    st.markdown("### 🧠 멘탈 & 라이프스타일")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        pos_lang_count = st.number_input("🗣️ 긍정 언어 사용 횟수", min_value=0, max_value=100, value=0, step=1)
    with col_m2:
        mood_state = st.selectbox(
            "🧭 오늘의 마음 상태",
            ["매우불쾌", "불쾌", "약간불쾌", "보통", "약간즐거움", "즐거움", "매우즐거움"],
            index=3 # '보통'을 기본값으로 설정
        )

    submit_button = st.form_submit_button("💾 기록 저장하기")

# ==========================================
# 💾 DB 저장 로직 (UPSERT)
# ==========================================
if submit_button:
    date_str = target_date.strftime('%Y-%m-%d')
    
    conn = sqlite3.connect("hx_health.db")
    cur = conn.cursor()
    
    # 이미 해당 날짜에 데이터가 있으면 업데이트(수정)하고, 없으면 새로 삽입(Insert)하는 안전한 쿼리
    query = """
    INSERT INTO daily_logs (date, bloating_b, acid_a, cough_c, pos_lang_count, mood_state)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(date) DO UPDATE SET
        bloating_b = excluded.bloating_b,
        acid_a = excluded.acid_a,
        cough_c = excluded.cough_c,
        pos_lang_count = excluded.pos_lang_count,
        mood_state = excluded.mood_state
    """
    
    cur.execute(query, (date_str, bloating_b, acid_a, cough_c, pos_lang_count, mood_state))
    conn.commit()
    conn.close()
    
    st.success(f"✅ {date_str}의 기록이 성공적으로 저장되었습니다! 좌측 메뉴에서 '종합 대시보드'를 확인해 보세요.")