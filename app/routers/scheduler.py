from fastapi import APIRouter, HTTPException
from database import get_db_connection
from typing import List
from datetime import datetime, time

router = APIRouter()

def str_to_time(time_str: str) -> time:
    """시간 문자열을 time 객체로 변환 (24시 이상 처리)"""
    hours, minutes, seconds = map(int, time_str.split(':'))
    if hours >= 24:
        hours -= 24
    return time(hours, minutes, seconds)

def interpolate_time(t1: time, t2: time, cdf1: float, cdf2: float, target_cdf: float) -> time:
    """선형 보간법으로 목표 CDF 값에 해당하는 시간을 계산"""
    # time 객체를 초로 변환
    t1_seconds = (t1.hour * 3600 + t1.minute * 60 + t1.second)
    t2_seconds = (t2.hour * 3600 + t2.minute * 60 + t2.second)
    
    # t2가 t1보다 작은 경우 (자정을 넘어가는 경우) 24시간을 더해줌
    if t2_seconds < t1_seconds:
        t2_seconds += 24 * 3600
    
    # 선형 보간
    if abs(cdf2 - cdf1) < 1e-10:  # CDF 값이 너무 가까운 경우
        interpolated_seconds = t1_seconds  # 첫 번째 시간 사용
    else:
        ratio = (target_cdf - cdf1) / (cdf2 - cdf1)
        interpolated_seconds = t1_seconds + (t2_seconds - t1_seconds) * ratio
    
    # 24시간으로 정규화
    while interpolated_seconds >= 24 * 3600:
        interpolated_seconds -= 24 * 3600
    
    # 초를 time 객체로 변환
    hours = int(interpolated_seconds // 3600)
    minutes = int((interpolated_seconds % 3600) // 60)
    seconds = int(interpolated_seconds % 60)
    
    return time(hours, minutes, seconds)

@router.get("/line/{line_id}/departure-times")
async def get_departure_times(line_id: int, bound_to: int):
    with get_db_connection() as (conn, cur):
        try:
            # 해당 노선의 열차 수 조회
            cur.execute("SELECT COUNT(*) FROM train WHERE line_ID = %s", (line_id,))
            N = cur.fetchone()[0]
            
            if N == 0:
                raise HTTPException(status_code=404, detail="No trains found for this line")
            
            if bound_to not in [1, 0]:
                raise HTTPException(status_code=400, detail="Invalid bound_to value")
            
            # 해당 노선의 route_shape 조회
            cur.execute("SELECT route_shape FROM line WHERE ID = %s", (line_id,))
            route_shape = cur.fetchone()[0]

            if route_shape == 'CIRCULAR':
                cur.execute("CALL GetCircularHistogram(%s, %s)", (line_id, bound_to))
            else:
                cur.execute("CALL GetRoundTripHistogram(%s)", (line_id))
            
            histogram_data = cur.fetchall()
            
            # 다음 결과셋 비우기 (여러 결과 반환될 우려)
            while cur.nextset():
                pass
            
            # CDF 데이터 준비
            times = []
            cdfs = []
            for row in histogram_data:
                times.append(str_to_time(str(row[0])))  # 문자열을 time 객체로 변환
                cdfs.append(float(row[3]))   # CDF 값을 float으로 변환

            # 목표 CDF 값들 (1/N, 2/N, ..., N/N)
            target_cdfs = [i / N for i in range(N)]
            
            # 각 목표 CDF 값에 대한 보간된 시간 계산
            result = []
            current_index = 1  # 현재 검사 중인 시간 구간의 인덱스
            
            for target_cdf in target_cdfs:

                # 현재 구간부터 시작하여 목표 CDF를 포함하는 구간 찾기
                while current_index < (len(cdfs) - 1) and cdfs[current_index] < target_cdf:
                    current_index += 1

                # 현재 구간에서 보간
                interpolated_time = interpolate_time(
                    times[current_index-1], times[current_index],
                    cdfs[current_index-1], cdfs[current_index],
                    target_cdf
                )
                result.append({
                    "departure_time": interpolated_time.strftime("%H:%M:%S"),
                    "cdf_value": round(target_cdf, 4)
                })
            
            cur.execute("""
                SELECT station.name, eta.ET FROM eta, station
                WHERE eta.station_ID = station.ID
                AND station.line_ID = %s
            """, (line_id,))

            etas = cur.fetchall()
            result_2 = []
            for eta in etas:
                total_seconds = int(eta[1].total_seconds())  # timedelta를 초로 변환
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                formatted_et = f"{minutes:02d}:{seconds:02d}"  # MM:SS 형식으로 변환
                result_2.append({
                    "station_name": eta[0],
                    "et": formatted_et
                })
            
            return {
                "line_id": line_id,
                "train_count": N,
                "departure_times": result,
                "etas": result_2,
                "route_shape": route_shape
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
