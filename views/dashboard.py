import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.title("📊 HX System Dashboard")
st.markdown("---")

# ==========================================
# 💾 1. 데이터 로드 및 전처리
# ==========================================
def load_data():
    conn = sqlite3.connect("hx_health.db")
    df = pd.read_sql_query("SELECT * FROM daily_logs ORDER BY date ASC", conn)
    conn.close()
    
    if not df.empty:
        df['date_obj'] = pd.to_datetime(df['date']).dt.date
    return df

df = load_data()

if not df.empty:
    
    # ==========================================
    # 🗓️ 2. 기간 필터링 UI
    # ==========================================
    st.write("🗓 **데이터 조회 기간 설정**")
    
    # [수정됨] "어제" 옵션 추가
    filter_option = st.selectbox(
        "분석할 기간을 선택하세요:",
        ["오늘", "어제", "지난 7일", "지난 30일", "지난 분기 (90일)", "지난 해 (365일)", "커스텀 기간 선택"],
        label_visibility="collapsed"
    )
    
    today = datetime.now().date()
    start_date = today
    end_date = today

    if filter_option == "오늘": 
        start_date = today
    elif filter_option == "어제": # [수정됨] 어제 날짜 계산 로직 추가
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif filter_option == "지난 7일": start_date = today - timedelta(days=7)
    elif filter_option == "지난 30일": start_date = today - timedelta(days=30)
    elif filter_option == "지난 분기 (90일)": start_date = today - timedelta(days=90)
    elif filter_option == "지난 해 (365일)": start_date = today - timedelta(days=365)
    elif filter_option == "커스텀 기간 선택":
        date_range = st.date_input("조회할 시작일과 종료일을 선택하세요", [today - timedelta(days=7), today])
        if len(date_range) == 2:
            start_date, end_date = date_range[0], date_range[1]
        else:
            start_date, end_date = date_range[0], date_range[0]
    else: 
        start_date = df['date_obj'].min()

    # 데이터 필터링 실행
    mask = (df['date_obj'] >= start_date) & (df['date_obj'] <= end_date)
    filtered_df = df.loc[mask].drop(columns=['date_obj'])

    # ==========================================
    # 🚀 3. 대시보드 렌더링 시작
    # ==========================================
    if not filtered_df.empty:
        
        # ---------------------------------------------------------
        # 🚨 Tactical Health Status (염증 신호등 & 간 회복 목표)
        # ---------------------------------------------------------
        st.markdown("### 🚨 Tactical Health Status")
        
        # [Hotfix] 안전한 평균 계산 함수 (NaN 방어)
        def get_safe_mean(series):
            val = pd.to_numeric(series, errors='coerce').mean()
            return 0.0 if pd.isna(val) else val

        # 1. 염증 조기 경보 - 선택된 기간의 '일평균' 데이터
        avg_b = get_safe_mean(filtered_df.get('bloating_b', pd.Series(dtype=float)))
        avg_a = get_safe_mean(filtered_df.get('acid_a', pd.Series(dtype=float)))
        avg_c = get_safe_mean(filtered_df.get('cough_c', pd.Series(dtype=float)))
        avg_upf = get_safe_mean(filtered_df.get('upf_count', pd.Series(dtype=float)))
        
        avg_bac_score = avg_b + avg_a + avg_c
        
        # 신호등 로직 판별
        if avg_bac_score > 5 or avg_upf >= 2:
            st.error(f"**🔴 위험 (염증 경보)** : 선택 기간 일평균 B-A-C 총점 {avg_bac_score:.1f}점, UPF {avg_upf:.1f}회\n\n내장지방 염증 수치가 높습니다. **즉시 식단 락다운 및 휴식을 취하세요!**")
        elif avg_bac_score > 2 or avg_upf >= 1:
            st.warning(f"**🟡 주의 (식단 관리)** : 선택 기간 일평균 B-A-C 총점 {avg_bac_score:.1f}점, UPF {avg_upf:.1f}회\n\n약간의 역류 증상 또는 초가공식품 섭취가 감지되었습니다. 오늘 저녁은 가볍게 드세요.")
        else:
            st.success(f"**🟢 양호 (간 회복 중)** : 선택 기간 일평균 B-A-C 총점 {avg_bac_score:.1f}점, UPF {avg_upf:.1f}회\n\n염증 유발 요인이 완벽히 통제되고 있습니다. 간이 안정적으로 회복되는 중입니다!")
            
        # 2. 간 회복 버다운 (Liver Recovery Burndown) UI
        col_tg, col_alt = st.columns(2)
        with col_tg:
            st.metric(label="🩸 중성지방 (TG) 목표", value="260 mg/dL", delta="-110 to Target (목표: 150미만)", delta_color="inverse")
        with col_alt:
            st.metric(label="🧪 간수치 (ALT) 목표", value="52 U/L", delta="-12 to Target (목표: 40미만)", delta_color="inverse")
            
        st.divider()
        
        # ---------------------------------------------------------
        # 🔥 Zone 2 지방 연소 가이드 (간 해독 엔진)
        # ---------------------------------------------------------
        st.markdown("### 🔥 간 해독 엔진 (Zone 2 지방 연소)")
        
        # exercise_min을 Zone 2(지방 연소) 시간으로 활용 (NaN 방어)
        avg_exercise = get_safe_mean(filtered_df.get('exercise_min', pd.Series(dtype=float)))
        
        # 목표: 하루 45분
        zone2_goal = 45.0
        progress_pct = min(avg_exercise / zone2_goal, 1.0) # 최대 100%까지만
        progress_pct = max(progress_pct, 0.0) # 혹시 모를 음수값 방어
        
        col_fire, col_text = st.columns([1, 2])
        with col_fire:
            st.metric(
                label="🏃 평균 지방 연소 시간", 
                value=f"{avg_exercise:.0f} 분", 
                delta=f"목표치(45분) 대비 {avg_exercise - zone2_goal:.0f}분",
                delta_color="normal" if avg_exercise >= zone2_goal else "inverse"
            )
            
        with col_text:
            st.progress(progress_pct)
            if avg_exercise >= zone2_goal:
                st.success("🎉 **엔진 풀가동!** 충분한 중강도 활동으로 간에 쌓인 지방을 효과적으로 태웠습니다.")
            elif avg_exercise >= 20:
                st.info("🔥 **연소 시작!** 엔진이 예열되었습니다. 하루 45분을 채우면 내장지방이 타기 시작합니다.")
            else:
                st.warning("🔋 **엔진 정지** 간 해독을 위해 약간 숨이 찰 정도(Zone 2)의 걷기가 필요합니다.")
                
        st.divider()
        # ---------------------------------------------------------

        # 마음 상태 매핑 (텍스트 -> 숫자)
        mood_mapping = {"매우불쾌": 1, "불쾌": 2, "약간불쾌": 3, "보통": 4, "약간즐거움": 5, "즐거움": 6, "매우즐거움": 7}
        reverse_mood = {1: "매우불쾌 🤬", 2: "불쾌 😠", 3: "약간불쾌 😕", 4: "보통 😐", 5: "약간즐거움 🙂", 6: "즐거움 😄", 7: "매우즐거움 🤩"}
        
        filtered_df['mood_score'] = filtered_df['mood_state'].map(mood_mapping)
        df['mood_score'] = df['mood_state'].map(mood_mapping)
        
        # 숫자형 데이터 안전 변환
        num_cols = ['bloating_b', 'acid_a', 'cough_c', 'upf_count', 'pos_lang_count', 'mood_score', 'hrv', 'sleep_hours', 'active_energy', 'exercise_min', 'stand_hours']
        for col in num_cols:
            if col in filtered_df.columns:
                filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # --- [상단] 평균 마음 상태 ---
        st.markdown("### 🧠 평균 마음 상태 (Average Mood)")
        if not filtered_df['mood_score'].dropna().empty:
            avg_mood = filtered_df['mood_score'].mean()
            closest_mood = int(round(avg_mood))
            mood_label = reverse_mood.get(closest_mood, "알 수 없음")
            
            st.markdown(f"#### **{mood_label}** (평균 {avg_mood:.2f}점 / 7.00점)")
            st.progress(avg_mood / 7.0) 
        else:
            st.info("선택한 기간 내 마음 상태 데이터가 없습니다.")

        st.divider()

        # --- [중단] 기간 요약 (Median/Min/Max) ---
        st.markdown("### 📌 선택 기간 요약")
        def draw_metric_card(title, col_name, df_target, unit=""):
            if col_name in df_target.columns and not df_target[col_name].dropna().empty:
                median_val = df_target[col_name].median()
                min_val = df_target[col_name].min()
                max_val = df_target[col_name].max()
                st.metric(label=title, value=f"{median_val:.2f}{unit}", delta=f"Min: {min_val:.2f} | Max: {max_val:.2f}", delta_color="off")
            else:
                st.metric(label=title, value="-", delta="데이터 없음", delta_color="off")

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

        st.info("""
        **💡 핵심 지표 벤치마크 및 가이드**
        * **💓 HRV:** 자율신경계 회복력. 높을수록 부교감신경 활성화(휴식 상태).
        * **💤 수면 시간:** 식도 점막 염증 치료의 핵심. (권장: 7~9시간)
        * **🍩 UPF (초가공식품):** 염증 및 위산 역류의 주범. (권장: 주 3회 이하)
        """)
        st.divider()

       # --- [하단] 최근 14일 트렌드 (Daily) ---
        st.markdown("### 📈 최근 14일 트렌드 (Daily Trend)")
        st.caption("최근 2주간의 일일 데이터를 통해 생활 습관과 증상의 즉각적인 변화를 추적합니다.")
        
        trend_df = df.copy()
        trend_df['date'] = pd.to_datetime(trend_df['date'])
        trend_df = trend_df.set_index('date')
        
        # 주간 평균을 내던 resample('W')를 제거하고, 일간 데이터의 최근 14일을 바로 가져옵니다.
        recent_14_df = trend_df[num_cols].tail(14)
        recent_14_df.index = recent_14_df.index.strftime('%Y-%m-%d')

        tab_m1, tab_m2, tab_m3, tab_m4 = st.tabs(["🚨 증상 흐름", "🧠 멘탈 & 라이프", "🔋 회복 지표", "🏃‍♂️ 활동량"])
        
        with tab_m1:
            st.write("**🤢 더부룩함 (B)**")
            if 'bloating_b' in recent_14_df.columns and not recent_14_df['bloating_b'].dropna().empty: st.line_chart(recent_14_df[['bloating_b']])
            st.write("**🔥 신물/쓰림 (A)**")
            if 'acid_a' in recent_14_df.columns and not recent_14_df['acid_a'].dropna().empty: st.line_chart(recent_14_df[['acid_a']])
            st.write("**🗣️ 잔기침 (C)**")
            if 'cough_c' in recent_14_df.columns and not recent_14_df['cough_c'].dropna().empty: st.line_chart(recent_14_df[['cough_c']])
                
        with tab_m2:
            st.write("**🍩 UPF 섭취 빈도 (횟수)**")
            if 'upf_count' in recent_14_df.columns:
                upf_data = recent_14_df[['upf_count']].fillna(0)
                if upf_data['upf_count'].sum() > 0: st.bar_chart(upf_data)
            st.write("**🗣️ 긍정 언어 사용 (횟수)**")
            if 'pos_lang_count' in recent_14_df.columns and not recent_14_df['pos_lang_count'].dropna().empty: st.line_chart(recent_14_df[['pos_lang_count']])
            st.write("**🧠 마음 상태 (1~7점)**")
            if 'mood_score' in recent_14_df.columns and not recent_14_df['mood_score'].dropna().empty: st.line_chart(recent_14_df[['mood_score']])
                
        with tab_m3:
            st.write("**💓 HRV (심박변이도, ms)**")
            if 'hrv' in trend_df.columns:
                valid_hrv = trend_df[['hrv']].dropna().tail(14) # 결측치 제거 후 최근 14개 추출
                if not valid_hrv.empty: 
                    valid_hrv.index = valid_hrv.index.strftime('%Y-%m-%d')
                    st.line_chart(valid_hrv)
            st.write("**💤 수면 시간 (시간)**")
            if 'sleep_hours' in trend_df.columns:
                valid_sleep = trend_df[['sleep_hours']].dropna().tail(14)
                if not valid_sleep.empty: 
                    valid_sleep.index = valid_sleep.index.strftime('%Y-%m-%d')
                    st.bar_chart(valid_sleep)
                
        with tab_m4:
            st.write("**🔥 활동 에너지 (kcal)**")
            if 'active_energy' in trend_df.columns:
                valid_energy = trend_df[['active_energy']].dropna().tail(14)
                if not valid_energy.empty: 
                    valid_energy.index = valid_energy.index.strftime('%Y-%m-%d')
                    st.area_chart(valid_energy)
                
            c_act1, c_act2 = st.columns(2)
            with c_act1:
                st.write("**🏃‍♂️ 운동 시간 (분)**")
                if 'exercise_min' in trend_df.columns:
                    valid_ex = trend_df[['exercise_min']].dropna().tail(14)
                    if not valid_ex.empty: 
                        valid_ex.index = valid_ex.index.strftime('%Y-%m-%d')
                        st.bar_chart(valid_ex)
            with c_act2:
                st.write("**🧍‍♂️ 일어서기 (시간)**")
                if 'stand_hours' in trend_df.columns:
                    valid_stand = trend_df[['stand_hours']].dropna().tail(14)
                    if not valid_stand.empty: 
                        valid_stand.index = valid_stand.index.strftime('%Y-%m-%d')
                        st.bar_chart(valid_stand)

        with st.expander("🗄️ 필터링된 데이터베이스 로그"):
            st.dataframe(filtered_df.style.format(precision=2))
    else:
        st.warning("선택하신 기간에 해당하는 데이터가 없습니다.")
else:
    st.info("아직 충분한 데이터가 없습니다. 먼저 수동 로그를 기록해 주세요.")