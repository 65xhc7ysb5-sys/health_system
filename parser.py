import xml.etree.ElementTree as ET
import sqlite3
import pandas as pd
from datetime import datetime

def parse_apple_health(xml_path):
    print(f"🔄 1. XML 파싱 시작: {xml_path} (수십만 건의 데이터를 스캔합니다...)")
    
    # 추출할 애플 건강 데이터 고유 식별자 매핑
    target_types = {
        'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'hrv',
        'HKQuantityTypeIdentifierDietaryWater': 'water_intake',
        'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_energy',
        'HKQuantityTypeIdentifierAppleExerciseTime': 'exercise_min',
        'HKCategoryTypeIdentifierAppleStandHour': 'stand_hours',
        'HKCategoryTypeIdentifierSleepAnalysis': 'sleep_hours'
    }

    records = []
    
    # iterparse: 대용량 XML을 메모리 과부하 없이 한 줄씩 읽는 아키텍트의 방식
    context = ET.iterparse(xml_path, events=('end',))
    
    for event, elem in context:
        if elem.tag == 'Record':
            r_type = elem.get('type')
            if r_type in target_types:
                date_str = elem.get('startDate')[:10] # YYYY-MM-DD 추출
                value = elem.get('value')
                
                # 수면 데이터 처리
                if r_type == 'HKCategoryTypeIdentifierSleepAnalysis':
                    if 'Asleep' in str(value) or 'InBed' in str(value):
                        try:
                            start = datetime.strptime(elem.get('startDate')[:19], '%Y-%m-%d %H:%M:%S')
                            end = datetime.strptime(elem.get('endDate')[:19], '%Y-%m-%d %H:%M:%S')
                            sleep_val = (end - start).total_seconds() / 3600
                            records.append({'date': date_str, 'type': 'sleep_hours', 'value': sleep_val})
                        except Exception: pass
                        
                # 📌 일어서기 데이터 처리 (추가된 부분)
                elif r_type == 'HKCategoryTypeIdentifierAppleStandHour':
                    if 'Stood' in str(value): # 일어선 시간(Stood)만 1시간으로 카운트
                        records.append({'date': date_str, 'type': 'stand_hours', 'value': 1})
                        
                # 나머지 일반 데이터 (HRV, 에너지, 운동, 물)
                else:
                    try:
                        records.append({'date': date_str, 'type': target_types[r_type], 'value': float(value)})
                    except Exception: pass
        elem.clear() # 메모리 해제 (매우 중요)

    df = pd.DataFrame(records)
    if df.empty:
        print("⚠️ 파싱된 데이터가 없습니다.")
        return pd.DataFrame()

    print("📊 2. 데이터 집계(Aggregation) 중...")
    # HRV는 하루 측정치의 '평균(mean)'을 구하고, 나머지는 모두 '합산(sum)' 처리
    hrv_df = df[df['type'] == 'hrv'].groupby('date')['value'].mean()
    others_df = df[df['type'] != 'hrv'].groupby(['date', 'type'])['value'].sum().unstack()
    
    # 두 데이터를 병합
    pivot_df = pd.concat([hrv_df.rename('hrv'), others_df], axis=1).reset_index()
    print(f"✅ 데이터 변환 완료: 총 {len(pivot_df)}일치 데이터가 정제되었습니다.")
    
    return pivot_df

def update_db(df):
    if df.empty:
        return
        
    print("🗄️ 3. 로컬 DB(SQLite)에 안전하게 적재(Merge)합니다...")
    conn = sqlite3.connect("hx_health.db")
    cur = conn.cursor()
    
    cols_to_update = [c for c in df.columns if c != 'date']
    success_count = 0
    
    for _, row in df.iterrows():
        date = row['date']
        
        # [안전장치 1] 해당 날짜의 행이 없다면 먼저 빈 행을 만듭니다. (수동 입력을 안 했던 과거 날짜들용)
        cur.execute("INSERT OR IGNORE INTO daily_logs (date) VALUES (?)", (date,))
        
        # [안전장치 2] 파싱된 객관적 지표만 콕 집어서 업데이트합니다. (B, A, C 등 수동 지표 보존)
        set_clauses = []
        values = []
        for col in cols_to_update:
            if pd.notna(row[col]): # 데이터가 존재하는 경우에만
                set_clauses.append(f"{col} = ?")
                values.append(row[col])
        
        if set_clauses:
            query = f"UPDATE daily_logs SET {', '.join(set_clauses)} WHERE date = ?"
            values.append(date)
            cur.execute(query, tuple(values))
            success_count += 1
            
    conn.commit()
    conn.close()
    print(f"🚀 로컬 DB 업데이트 완료! (총 {success_count}일치 데이터가 성공적으로 병합되었습니다.)")

if __name__ == "__main__":

    # 데이터 폴더 경로 지정
    data_file = "data/export.xml"

    try:
        data = parse_apple_health(data_file)
        update_db(data)
    except FileNotFoundError:
        print("❌ 'export.xml' 파일을 찾을 수 없습니다. hx-health-app 폴더 안에 파일이 있는지 확인해주세요.")