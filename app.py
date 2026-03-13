import streamlit as st
import sqlite3

# ==========================================
# 1. 페이지 통합 설정
# ==========================================
st.set_page_config(page_title="HX Architect", page_icon="🧠", layout="wide")

# ==========================================
# 2. DB 초기화 및 자기 복구 (Self-Healing) 엔진
# ==========================================
def init_db():
    conn = sqlite3.connect("hx_health.db")
    cur = conn.cursor()
    
    # 1) 메인 테이블 생성 (DB 파일이 삭제되었을 경우 뼈대부터 다시 만듦)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            date TEXT PRIMARY KEY,
            bloating_b INTEGER DEFAULT 0,
            acid_a INTEGER DEFAULT 0,
            cough_c INTEGER DEFAULT 0,
            pos_lang_count INTEGER DEFAULT 0,
            mood_state TEXT,
            upf_count INTEGER DEFAULT 0,
            hrv REAL,
            sleep_hours REAL,
            water_intake REAL,
            active_energy REAL,
            exercise_min REAL,
            stand_hours REAL
        )
    """)
    
    # 2) 확장 컬럼 마이그레이션 (기존 DB에 식단/AI 컬럼이 없을 경우 추가)
    try:
        cur.execute("ALTER TABLE daily_logs ADD COLUMN meals_text TEXT")
        cur.execute("ALTER TABLE daily_logs ADD COLUMN ai_warnings TEXT")
        cur.execute("ALTER TABLE daily_logs ADD COLUMN ai_recommends TEXT")
    except sqlite3.OperationalError:
        pass # 이미 컬럼이 존재하면 무시하고 넘어감
        
    conn.commit()
    conn.close()

# 앱이 시작될 때마다 무조건 DB 상태를 검증하고 초기화
init_db()

# ==========================================
# 3. 사이드바 및 네비게이션 라우팅 (아래는 기존 코드 그대로 유지)
# ==========================================

dashboard_page = st.Page("views/dashboard.py", title="종합 대시보드", icon="📊", default=True)
diet_page = st.Page("views/diet.py", title="AI 식단 관리", icon="🥗")
record_page = st.Page("views/record.py", title="수동 로그 기록", icon="✍️")

# 4. 네비게이션 메뉴 구조화 (사이드바에 렌더링됨)
pg = st.navigation({
    "System Monitor": [dashboard_page],
    "Data Management": [diet_page, record_page]
})

# 5. 선택된 페이지 실행
pg.run()