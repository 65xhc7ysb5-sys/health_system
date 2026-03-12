import sqlite3

def init_db():
    conn = sqlite3.connect("hx_health.db")
    cur = conn.cursor()
    
    # 통합 테이블: 주관적 지표 + 객관적 지표
    cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            date TEXT PRIMARY KEY,
            -- [주관적/수동 입력]
            bloating_b INTEGER,
            acid_a INTEGER,
            cough_c INTEGER,
            upf_count INTEGER,
            pos_lang_count INTEGER,
            mood_state TEXT,
            
            -- [객관적/자동 수집 가능 항목]
            water_intake REAL,
            hrv REAL,
            sleep_hours REAL,
            active_energy INTEGER, -- 움직이기(kcal)
            exercise_min INTEGER,  -- 운동하기(min)
            stand_hours INTEGER    -- 일어서기(hr)
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ 통합 Database 구조로 업데이트 완료!")

if __name__ == "__main__":
    init_db()