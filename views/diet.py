import streamlit as st
import sqlite3
import json
import google.generativeai as genai
from datetime import datetime

st.title("🥗 AI 식단 관리 및 UPF 추출 (Powered by Gemini)")
st.markdown("---")
st.caption("오늘 먹은 음식을 편하게 적어주세요. Gemini AI가 위장/역류 관점에서 식단을 분석하고 UPF(초가공식품) 빈도를 자동 추출합니다.")

# ==========================================
# 🔑 Gemini API 설정
# ==========================================
# secrets.toml에 저장된 키를 불러와 모델을 초기화합니다.
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 가볍고 빠르며 텍스트 분석에 탁월한 1.5 Flash 모델 사용
    model = genai.GenerativeModel('gemini-2.5-flash') 
except Exception as e:
    st.error("⚠️ API 키 설정 오류: .streamlit/secrets.toml 파일에 GEMINI_API_KEY를 설정했는지 확인해주세요.")
    st.stop()

# ==========================================
# 🗓 1. 날짜 선택 및 기존 데이터 불러오기
# ==========================================
target_date = st.date_input("식단 기록 날짜", datetime.now())
date_str = target_date.strftime('%Y-%m-%d')

conn = sqlite3.connect("hx_health.db")
cur = conn.cursor()
cur.execute("SELECT meals_text, ai_warnings, ai_recommends, upf_count FROM daily_logs WHERE date=?", (date_str,))
row = cur.fetchone()
conn.close()

existing_meals = row[0] if row and row[0] else ""
existing_warn = row[1] if row and row[1] else ""
existing_rec = row[2] if row and row[2] else ""
existing_upf = row[3] if row and row[3] else 0

# ==========================================
# ✍️ 2. 식단 입력 폼
# ==========================================
meals_input = st.text_area(
    "🍽️ 오늘의 식단 (아침, 점심, 저녁, 간식 등)", 
    value=existing_meals, 
    height=150, 
    placeholder="예: 아침은 굶음. 점심은 돈까스와 쫄면. 저녁은 샐러드와 닭가슴살. 간식으로 제로콜라 1캔과 과자 조금 먹음."
)

# ==========================================
# 🤖 3. Gemini AI 분석 및 DB 저장
# ==========================================
if st.button("🚀 AI 식단 분석 및 DB 저장"):
    if not meals_input.strip():
        st.warning("식단을 먼저 입력해주세요!")
    else:
        with st.spinner("Gemini 주치의가 식단을 분석 중입니다..."):
            
            # --- 프롬프트 엔지니어링 (Persona & JSON Output) ---
            prompt = f"""
            당신은 역류성 식도염(GERD), 인후두 역류(LPR), 소화불량을 전문으로 치료하는 소화기내과 전문의이자 영양사입니다.
            환자의 오늘 식단 일기를 분석하고, 위장 건강에 미치는 영향을 평가해주세요.

            환자 식단: "{meals_input}"

            아래 3가지 요소를 반드시 포함하여 분석해주세요:
            1. upf_count: 식단에 포함된 초가공식품(UPF)의 개수 (정수). (예: 과자, 햄버거, 콜라, 소시지, 라면, 튀김류 등)
            2. warnings: 위장/역류를 유발할 수 있는 음식에 대한 경고와 그 이유. (위산 분비 자극, 하부 식도 괄약근 이완 등 의학적 근거 포함)
            3. recommendations: 내일 위장을 편안하게 달래기 위한 구체적이고 부드러운 대체 식단 추천.

            응답은 반드시 아래의 JSON 형식으로만 작성하세요. 마크다운(` ```json `)이나 다른 설명은 절대 포함하지 마세요.
            {{
                "upf_count": 0,
                "warnings": "경고 메시지 텍스트",
                "recommendations": "추천 메시지 텍스트"
            }}
            """

            try:
                # Gemini API 호출
                response = model.generate_content(prompt)
                response_text = response.text.strip()
                
                # 마크다운 찌꺼기(```json 등)가 붙어올 경우를 대비한 텍스트 정제
                if response_text.startswith("```json"):
                    response_text = response_text[7:-3]
                elif response_text.startswith("```"):
                    response_text = response_text[3:-3]
                    
                # JSON 파싱
                ai_data = json.loads(response_text)
                
                extracted_upf = int(ai_data.get("upf_count", 0))
                ai_warnings = ai_data.get("warnings", "경고를 분석할 수 없습니다.")
                ai_recommends = ai_data.get("recommendations", "추천을 분석할 수 없습니다.")

                # DB 업데이트
                conn = sqlite3.connect("hx_health.db")
                cur = conn.cursor()
                query = """
                INSERT INTO daily_logs (date, meals_text, ai_warnings, ai_recommends, upf_count)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    meals_text = excluded.meals_text,
                    ai_warnings = excluded.ai_warnings,
                    ai_recommends = excluded.ai_recommends,
                    upf_count = excluded.upf_count
                """
                cur.execute(query, (date_str, meals_input, ai_warnings, ai_recommends, extracted_upf))
                conn.commit()
                conn.close()
                
                st.success(f"✅ Gemini 분석 완료! 추출된 UPF 지수({extracted_upf}회)가 대시보드에 자동 반영되었습니다.")
                st.rerun()

            except json.JSONDecodeError:
                st.error("⚠️ AI가 올바른 JSON 형식을 반환하지 않았습니다. 다시 시도해 주세요.")
                st.write(f"Raw Response: {response.text}")
            except Exception as e:
                st.error(f"⚠️ API 통신 중 오류가 발생했습니다: {str(e)}")

# ==========================================
# 🩺 4. 분석 결과 (피드백) 출력
# ==========================================
if existing_warn or existing_rec:
    st.divider()
    st.markdown(f"### 🤖 Gemini 주치의 피드백 (추출된 UPF: **{existing_upf}회**)")
    st.warning(existing_warn)
    st.info(existing_rec)