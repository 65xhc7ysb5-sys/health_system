import streamlit as st
import sqlite3

# 1. 페이지 통합 설정 (모든 페이지에 공통으로 적용됨)
st.set_page_config(page_title="HX Architect", page_icon="🧠", layout="wide")

# 2. DB 안전장치 (앱이 켜질 때 필요한 컬럼이 없으면 자동 생성)
def upgrade_db():
    conn = sqlite3.connect("hx_health.db")
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE daily_logs ADD COLUMN meals_text TEXT")
        cur.execute("ALTER TABLE daily_logs ADD COLUMN ai_warnings TEXT")
        cur.execute("ALTER TABLE daily_logs ADD COLUMN ai_recommends TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # 이미 컬럼이 존재하면 패스
    conn.close()

upgrade_db()

# 3. 각 독립된 페이지 정의 (경로, 제목, 아이콘)
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