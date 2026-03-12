import streamlit as st
import sqlite3
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="HX Architect", page_icon="🧠")

def save_entry(data):
    conn = sqlite3.connect("hx_health.db")
    cur = conn.cursor()
    
    # 1. 시스템 안전장치 (Self-Healing): 테이블이 없으면 자동으로 생성합니다.
    cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            date TEXT PRIMARY KEY,
            bloating_b INTEGER,
            acid_a INTEGER,
            cough_c INTEGER,
            upf_count INTEGER,
            pos_lang_count INTEGER,
            mood_state TEXT,
            water_intake REAL,
            hrv REAL,
            sleep_hours REAL,
            active_energy INTEGER,
            exercise_min INTEGER,
            stand_hours INTEGER
        )
    ''')
    
    # 2. 아키텍트의 데이터 보호 로직 (UPSERT)
    # INSERT OR REPLACE를 쓰면 나중에 파서가 넣은 건강 데이터(hrv 등)가 통째로 날아갈 수 있습니다.
    # 따라서 수동 입력한 컬럼만 콕 집어서 업데이트(ON CONFLICT DO UPDATE) 합니다.
    cur.execute('''
        INSERT INTO daily_logs (date, bloating_b, acid_a, cough_c, upf_count, pos_lang_count, mood_state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            bloating_b = excluded.bloating_b,
            acid_a = excluded.acid_a,
            cough_c = excluded.cough_c,
            upf_count = excluded.upf_count,
            pos_lang_count = excluded.pos_lang_count,
            mood_state = excluded.mood_state
    ''', data)
    
    conn.commit()
    conn.close()
    

st.title("🧠 HX Health System v3.0")
st.markdown("---")

# 1. 데이터 추출(Extract) 섹션
with st.form("daily_log_form", clear_on_submit=True):
    date = st.date_input("날짜 선택", datetime.now())
    
    col1, col2, col3 = st.columns(3)
    b = col1.select_slider("더부룩함(B)", options=[0, 1, 2, 3])
    a = col2.select_slider("신물(A)", options=[0, 1, 2, 3])
    c = col3.select_slider("잔기침(C)", options=[0, 1, 2, 3])
    
    st.markdown("---")
    upf = st.number_input("UPF(초가공식품) 횟수", 0, 10, 0)
    pos = st.number_input("긍정 언어 사용 횟수", 0, 100, 0)
    mood = st.select_slider("마음 상태", options=["매우불쾌", "불쾌", "약간불쾌", "보통", "약간즐거움", "즐거움", "매우즐거움"], value="보통")
    
    # 2. 적재(Load) 실행
    if st.form_submit_button("시스템 커밋 (Save Log)"):
        payload = (date.strftime('%Y-%m-%d'), b, a, c, upf, pos, mood)
        save_entry(payload)
        st.success(f"✅ {date} 데이터가 로컬 DB에 성공적으로 로드되었습니다.")