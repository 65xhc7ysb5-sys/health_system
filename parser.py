import xml.etree.ElementTree as ET
import sqlite3
import pandas as pd
from datetime import datetime

def parse_apple_health(xml_path):
    print(f"🔄 파싱 시작: {xml_path}...")
    
    # 우리가 수집할 매핑 테이블
    target_types = {
        'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'hrv',
        'HKQuantityTypeIdentifierDietaryWater': 'water_intake',
        'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_energy',
        'HKCategoryTypeIdentifierSleepAnalysis': 'sleep_hours'
    }

    records = []

    # 메모리 효율을 위해 iterparse 사용
    context = ET.iterparse(xml_path, events=('end',))
    
    for event, elem in context:
        if elem.tag == 'Record':
            r_type = elem.get('type')
            if r_type in target_types:
                # 날짜 변환 (2026-03-12 23:10:05 +0900 -> 2026-03-12)
                raw_date = elem.get('startDate')
                date_str = raw_date[:10]
                
                # 값 추출
                value = elem.get('value')
                
                # 수면 데이터 처리 (수면은 value가 없는 경우가 많아 시작/종료 시간차로 계산)
                if r_type == 'HKCategoryTypeIdentifierSleepAnalysis':
                    if elem.get('value') == 'HKCategoryValueSleepAnalysisInBed':
                        start = datetime.strptime(elem.get('startDate')[:19], '%Y-%m-%d %H:%M:%S')
                        end = datetime.strptime(elem.get('endDate')[:19], '%Y-%m-%d %H:%M:%S')
                        value = (end - start).total_seconds() / 3600 # 시간 단위 변환
                    else:
                        continue # InBed 데이터만 사용

                records.append({
                    'date': date_str,
                    'type': target_types[r_type],
                    'value': float(value) if value else 0
                })
        
        # 메모리 확보를 위해 처리한 요소 제거
        elem.clear()

    # 데이터 가공 (Transform)
    df = pd.DataFrame(records)
    # 날짜별, 타입별 합산 (하루에 여러 번 측정된 값 처리)
    pivot_df = df.groupby(['date', 'type'])['value'].sum().unstack().reset_index()
    
    print("✅ 데이터 변환 완료:")
    print(pivot_df.tail()) # 최근 5일치 데이터 출력 테스트
    return pivot_df

def load_to_db(df):
    conn = sqlite3.connect("hx_health.db")
    # 1. 임시 테이블에 로드
    df.to_sql('health_temp', conn, if_exists='replace', index=False)
    
    # 2. SQL UPSERT (기존 daily_logs 테이블의 해당 날짜 컬럼만 업데이트)
    cur = conn.cursor()
    cols = [c for c in df.columns if c != 'date']
    for col in cols:
        query = f"""
        UPDATE daily_logs 
        SET {col} = (SELECT {col} FROM health_temp WHERE health_temp.date = daily_logs.date)
        WHERE EXISTS (SELECT 1 FROM health_temp WHERE health_temp.date = daily_logs.date)
        """
        cur.execute(query)
    
    conn.commit()
    conn.close()
    print("🚀 DB 업데이트 완료!")

if __name__ == "__main__":
    # 테스트 실행
    try:
        data = parse_apple_health("export.xml")
        load_to_db(data)
    except FileNotFoundError:
        print("❌ export.xml 파일을 찾을 수 없습니다. 프로젝트 폴더에 넣어주세요.")