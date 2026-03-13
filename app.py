import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

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


# --- 📊 대시보드 시작 ---
st.markdown("---")
st.subheader("📊 HX System Dashboard")

def load_data():
    conn = sqlite3.connect("hx_health.db")
    df = pd.read_sql_query("SELECT * FROM daily_logs ORDER BY date ASC", conn)
    conn.close()
    
    # 필터링을 위해 date 컬럼을 실제 datetime 객체로 변환하는 임시 컬럼 생성
    if not df.empty:
        df['date_obj'] = pd.to_datetime(df['date']).dt.date
    return df

df = load_data()

if not df.empty:
    # 🗓️ 1. 기간 필터링 UI (컨트롤 패널)
    st.write("🗓 **데이터 조회 기간 설정**")
    
    filter_option = st.selectbox(
        "분석할 기간을 선택하세요:",
        ["전체 기간", "오늘", "지난 7일", "지난 30일", "지난 분기 (90일)", "지난 해 (365일)", "커스텀 기간 선택"]
    )
    
    today = datetime.now().date()
    start_date = today
    end_date = today

    # 선택된 옵션에 따른 날짜 계산
    if filter_option == "오늘":
        start_date = today
    elif filter_option == "지난 7일":
        start_date = today - timedelta(days=7)
    elif filter_option == "지난 30일":
        start_date = today - timedelta(days=30)
    elif filter_option == "지난 분기 (90일)":
        start_date = today - timedelta(days=90)
    elif filter_option == "지난 해 (365일)":
        start_date = today - timedelta(days=365)
    elif filter_option == "커스텀 기간 선택":
        # 커스텀 선택 시 달력 위젯 표시
        date_range = st.date_input("조회할 시작일과 종료일을 선택하세요", [today - timedelta(days=7), today])
        if len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            start_date = date_range[0]
            end_date = date_range[0]
    else: # "전체 기간"
        start_date = df['date_obj'].min()

    # ✂️ 2. 데이터 필터링 실행
    mask = (df['date_obj'] >= start_date) & (df['date_obj'] <= end_date)
    filtered_df = df.loc[mask].drop(columns=['date_obj']) # 필터링 후 임시 컬럼 제거

    if not filtered_df.empty:
        # 1. 마음 상태 매핑 및 그래픽 처리를 위한 딕셔너리
        mood_mapping = {"매우불쾌": 1, "불쾌": 2, "약간불쾌": 3, "보통": 4, "약간즐거움": 5, "즐거움": 6, "매우즐거움": 7}
        reverse_mood = {1: "매우불쾌 🤬", 2: "불쾌 😠", 3: "약간불쾌 😕", 4: "보통 😐", 5: "약간즐거움 🙂", 6: "즐거움 😄", 7: "매우즐거움 🤩"}
        
        filtered_df['mood_score'] = filtered_df['mood_state'].map(mood_mapping)
        df['mood_score'] = df['mood_state'].map(mood_mapping) # 13주 트렌드용 전체 데이터에도 적용
        
        # 2. 누락되었던 활동량 컬럼 복구 및 숫자형 안전 변환
        num_cols = ['bloating_b', 'acid_a', 'cough_c', 'upf_count', 'pos_lang_count', 'mood_score', 'hrv', 'sleep_hours', 'active_energy', 'exercise_min', 'stand_hours']
        for col in num_cols:
            if col in filtered_df.columns:
                filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # ==========================================
        # 🌟 1. 최상단: 현재 평균 마음 상태 (단독 하이라이트)
        # ==========================================
        st.markdown("### 🧠 평균 마음 상태 (Average Mood)")
        if not filtered_df['mood_score'].dropna().empty:
            avg_mood = filtered_df['mood_score'].mean()
            closest_mood = int(round(avg_mood))
            mood_label = reverse_mood.get(closest_mood, "알 수 없음")
            
            # 그래픽(Progress Bar)과 이모지로 직관적 표현
            st.markdown(f"#### **{mood_label}** (평균 {avg_mood:.2f}점 / 7.00점)")
            st.progress(avg_mood / 7.0) 
        else:
            st.info("선택한 기간 내 마음 상태 데이터가 없습니다.")

        st.divider()

        # ==========================================
        # 📌 2. 선택 기간 요약 (소수점 2자리 통일)
        # ==========================================
        st.markdown("### 📌 선택 기간 요약 (Median / Min / Max)")
        
        def draw_metric_card(title, col_name, df_target, unit=""):
            if col_name in df_target.columns and not df_target[col_name].dropna().empty:
                median_val = df_target[col_name].median()
                min_val = df_target[col_name].min()
                max_val = df_target[col_name].max()
                # 모든 수치를 소수점 2자리(0.00)로 포맷팅
                st.metric(label=title, value=f"{median_val:.2f}{unit}", delta=f"Min: {min_val:.2f} | Max: {max_val:.2f}", delta_color="off")
            else:
                st.metric(label=title, value="-", delta="데이터 없음", delta_color="off")

        # 4열로 나누어 활동량까지 전부 표기
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**🚨 위장/역류**")
            draw_metric_card("더부룩함(B)", "bloating_b", filtered_df)
            draw_metric_card("신물(A)", "acid_a", filtered_df)
            draw_metric_card("잔기침(C)", "cough_c", filtered_df)
        with c2:
            st.markdown("**🧠 멘탈/라이프**")
            draw_metric_card("UPF 빈도", "upf_count", filtered_df, "회")
            draw_metric_card("긍정 언어", "pos_lang_count", filtered_df, "회")
        with c3:
            st.markdown("**🔋 회복력**")
            draw_metric_card("수면 시간", "sleep_hours", filtered_df, "시간")
            draw_metric_card("HRV", "hrv", filtered_df, "ms")
        with c4:
            st.markdown("**🏃‍♂️ 활동량**")
            draw_metric_card("활동 에너지", "active_energy", filtered_df, "kcal")
            draw_metric_card("운동 시간", "exercise_min", filtered_df, "분")
            draw_metric_card("일어서기", "stand_hours", filtered_df, "시간")

        # ==========================================
        # 📚 3. 핵심 지표 벤치마크 가이드
        # ==========================================
        st.info("""
        **💡 핵심 지표 벤치마크 및 가이드 (Benchmarks & Meaning)**
        * **💓 HRV (심박변이도):** 자율신경계의 스트레스 회복력을 의미합니다. 수치가 높을수록 부교감신경이 활성화되어 몸(위장 포함)이 잘 쉬고 있다는 뜻입니다. (일반적 건강 목표: 40~100ms 이상이나 개인차가 크므로, 자신의 과거 평균보다 높게 유지하는 것이 핵심입니다.)
        * **💤 수면 시간:** 수면은 식도 점막 염증 치료와 위장 운동 리셋을 위한 필수 조건입니다. (성인 권장 벤치마크: 7~9시간)
        * **🍩 UPF (초가공식품):** 인공 첨가물, 방부제가 든 식품으로 장내 미생물 밸런스를 깨고 위산 역류를 일으키는 주범입니다. (권장 벤치마크: 주 3회 이하, 이상적 목표는 0회)
        """)
        st.divider()

        # ==========================================
        # 📈 4. 13주(1분기) 주간 매크로 트렌드 (차트 완전 분리 & 안정화 패치)
        # ==========================================
        st.markdown("### 📈 최근 13주 거시적 트렌드 (Weekly Average)")
        
        trend_df = df.copy()
        trend_df['date'] = pd.to_datetime(trend_df['date'])
        trend_df = trend_df.set_index('date')
        
        # 'W'(주간) 평균 계산 후 최근 13주만 추출
        weekly_df = trend_df[num_cols].resample('W').mean().tail(13)
        weekly_df.index = weekly_df.index.strftime('%Y-%m-%d')

        tab_m1, tab_m2, tab_m3, tab_m4 = st.tabs(["🚨 증상 흐름", "🧠 멘탈 & 라이프", "🔋 회복 지표", "🏃‍♂️ 활동량"])
        
        with tab_m1:
            st.markdown("**🚨 13주 개별 증상 흐름 (B, A, C)**")
            
            st.write("**🤢 더부룩함 (B)**")
            if 'bloating_b' in weekly_df.columns and not weekly_df['bloating_b'].dropna().empty:
                st.line_chart(weekly_df[['bloating_b']]) # DataFrame 형태로 강제 변환하여 안정성 확보
            else:
                st.caption("데이터 없음")
                
            st.write("**🔥 신물/쓰림 (A)**")
            if 'acid_a' in weekly_df.columns and not weekly_df['acid_a'].dropna().empty:
                st.line_chart(weekly_df[['acid_a']])
            else:
                st.caption("데이터 없음")
                
            st.write("**🗣️ 잔기침 (C)**")
            if 'cough_c' in weekly_df.columns and not weekly_df['cough_c'].dropna().empty:
                st.line_chart(weekly_df[['cough_c']])
            else:
                st.caption("데이터 없음")
                
        with tab_m2:
            st.write("**🍩 UPF 섭취 빈도 (횟수)**")
            if 'upf_count' in weekly_df.columns:
                # NaN을 0으로 채워서 Streamlit 렌더링 에러 방지
                upf_data = weekly_df[['upf_count']].fillna(0)
                if upf_data['upf_count'].sum() > 0:
                    st.bar_chart(upf_data)
                else:
                    st.caption("최근 13주간 데이터 없음")
            
            st.write("**🗣️ 긍정 언어 사용 (횟수)**")
            if 'pos_lang_count' in weekly_df.columns and not weekly_df['pos_lang_count'].dropna().empty:
                st.line_chart(weekly_df[['pos_lang_count']])
                
            st.write("**🧠 마음 상태 (1~7점)**")
            if 'mood_score' in weekly_df.columns and not weekly_df['mood_score'].dropna().empty:
                st.line_chart(weekly_df[['mood_score']])
                
        with tab_m3:
            st.write("**💓 HRV (심박변이도, ms)**")
            if 'hrv' in weekly_df.columns and not weekly_df['hrv'].dropna().empty:
                st.line_chart(weekly_df[['hrv']])
                
            # 💡 [핵심 패치] 수면 시간 렌더링 강제화
            st.write("**💤 수면 시간 (시간)**")
            if 'sleep_hours' in weekly_df.columns:
                sleep_data = weekly_df[['sleep_hours']].fillna(0) # 비어있는 주는 0시간으로 처리
                if sleep_data['sleep_hours'].sum() > 0:           # 13주 전체 합이 0보다 클 때만 그림
                    st.bar_chart(sleep_data)
                else:
                    st.caption("최근 13주간 수면 데이터가 없습니다.")
                
        with tab_m4:
            st.write("**🔥 활동 에너지 (kcal)**")
            if 'active_energy' in weekly_df.columns and not weekly_df['active_energy'].dropna().empty:
                st.area_chart(weekly_df[['active_energy']])
                
            c_act1, c_act2 = st.columns(2)
            with c_act1:
                st.write("**🏃‍♂️ 운동 시간 (분)**")
                if 'exercise_min' in weekly_df.columns:
                    ex_data = weekly_df[['exercise_min']].fillna(0)
                    if ex_data['exercise_min'].sum() > 0:
                        st.bar_chart(ex_data)
                    else:
                        st.caption("데이터 없음")
            with c_act2:
                st.write("**🧍‍♂️ 일어서기 (시간)**")
                if 'stand_hours' in weekly_df.columns:
                    stand_data = weekly_df[['stand_hours']].fillna(0)
                    if stand_data['stand_hours'].sum() > 0:
                        st.bar_chart(stand_data)
                    else:
                        st.caption("데이터 없음")

    else:
        st.warning("선택하신 기간에 해당하는 데이터가 없습니다.")