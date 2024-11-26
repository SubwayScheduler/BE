from fastapi import APIRouter, UploadFile, File, HTTPException
import csv
from fastapi.responses import StreamingResponse
from io import StringIO, BytesIO
from database import get_db_connection
from datetime import datetime, timedelta, time
from schemas import StationCreate, ETACreate, GarageCreate, CongestionCreate, PlatformCreate
from pydantic import ValidationError
import pymysql
from fastapi.responses import Response

router = APIRouter()

@router.post("/{line_id}/import/stations")
async def upload_stations(line_id: int, file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    content = await file.read()

    # encoding = detect(content).get('encoding', 'utf-8')
    encoding = 'euc-kr'

    text = content.decode(encoding)
    csv_file = StringIO(text)
    csv_reader = csv.DictReader(csv_file)

    def convert_time_format(time_str):
        try:
            # 입력값이 "분:초" 형식이라고 가정
            minutes, seconds = map(int, time_str.split(':'))
            # timedelta를 사용하여 올바른 시간으로 변환
            time = timedelta(hours=0, minutes=minutes, seconds=seconds)
            return (datetime.min + time).time().strftime('%H:%M:%S')
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Invalid time format: {time_str}")

    with get_db_connection() as (conn, cur):
        try:
            # 해당 Line의 기존 데이터 삭제
            cur.execute("DELETE FROM garage WHERE line_ID = %s", (line_id,))
            cur.execute("DELETE FROM eta WHERE station_ID IN (SELECT ID FROM station WHERE line_ID = %s)", (line_id,))
            cur.execute("DELETE FROM station WHERE line_ID = %s", (line_id,))

            for index, row in enumerate(csv_reader):
                try:
                    station_id = int(row.get('역번호'))
                    station_name = row.get('역명')
                    eta_str = row.get('소요시간')

                    if not all([station_id, station_name, eta_str]):
                        raise HTTPException(status_code=400, detail="Missing required fields")

                    # Station 데이터 검증
                    station_data = StationCreate(
                        name=station_name,
                        line_ID=line_id
                    )

                    # 시간 형식 변환
                    formatted_eta = convert_time_format(eta_str)

                    # ETA 데이터 검증
                    eta_data = ETACreate(
                        station_ID=station_id,
                        ET=formatted_eta
                    )

                    # Station 삽입
                    cur.execute(
                        "INSERT INTO station (ID, name, line_ID) VALUES (%s, %s, %s)",
                        (station_id, station_data.name, station_data.line_ID)
                    )
                    
                    # ETA 삽입
                    cur.execute(
                        "INSERT INTO eta (station_ID, ET) VALUES (%s, %s)",
                        (eta_data.station_ID, eta_data.ET.strftime('%H:%M:%S'))
                    )

                    # 첫 번째 역을 Garage로 설정
                    if index == 0:
                        garage_data = GarageCreate(
                            line_ID=line_id,
                            station_ID=station_id
                        )
                        cur.execute(
                            "INSERT INTO garage (line_ID, station_ID) VALUES (%s, %s)",
                            (garage_data.line_ID, garage_data.station_ID)
                        )

                except ValidationError as e:
                    raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

            conn.commit()
            return {"message": "Stations and ETAs uploaded successfully"}
        except Exception as e:
            conn.rollback()
            if isinstance(e, pymysql.Error):
                raise HTTPException(status_code=400, detail=str(e))
            else:
                raise HTTPException(status_code=500, detail=str(e))


@router.post("/{line_id}/import/congestion")
async def upload_congestion(line_id: int, file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    content = await file.read()
    # encoding = detect(content).get('encoding', 'utf-8')
    encoding = 'euc-kr'
    
    text = content.decode(encoding)
    csv_file = StringIO(text)
    csv_reader = csv.DictReader(csv_file)

    def convert_time_format(time_str: str) -> str:
        try:
            # 시간 형식이 "H:MM" 또는 "HH:MM"
            hours, minutes = map(int, time_str.split(':'))
            time = timedelta(hours=hours, minutes=minutes)
            return (datetime.min + time).time().strftime('%H:%M:%S')
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Invalid time format: {time_str}")

    with get_db_connection() as (conn, cur):
        try:
            # 해당 Line의 기존 데이터 삭제
            cur.execute("""
                DELETE FROM congestion 
                WHERE platform_station_ID IN (
                    SELECT ID FROM station WHERE line_ID = %s
                )
            """, (line_id,))
            cur.execute("""
                DELETE FROM platform 
                WHERE station_ID IN (
                    SELECT ID FROM station WHERE line_ID = %s
                )
            """, (line_id,))

            for row in csv_reader:
                try:
                    station_id = int(row['역번호'])
                    station_name = row['역명']
                    bound_to = row['상하구분']

                    if bound_to == '상선' or bound_to == '외선':
                        bound_to_value = 0
                    elif bound_to == '하선' or bound_to == '내선':
                        bound_to_value = 1
                    else:
                        raise HTTPException(status_code=400, detail=f"Invalid bound_to value: {bound_to}")

                    # Platform 데이터 검증
                    platform_data = PlatformCreate(
                        station_ID=station_id,
                        bound_to=bound_to_value
                    )

                    # Platform 삽입
                    cur.execute(
                        "INSERT INTO platform (station_ID, bound_to) VALUES (%s, %s)", 
                        (platform_data.station_ID, platform_data.bound_to)
                    )

                    # 시간대별 혼잡도 데이터 처리
                    time_slots = [col for col in row.keys() if ':' in col]
                    for time_slot in time_slots:
                        congestion_value = float(row[time_slot] or 0)
                        formatted_time = convert_time_format(time_slot)

                        # Congestion 데이터 검증
                        congestion_data = CongestionCreate(
                            platform_station_ID=station_id,
                            platform_bound_to=bound_to_value,
                            time_slot=datetime.strptime(formatted_time, '%H:%M:%S').time(),
                            congest_status=congestion_value
                        )

                        # Congestion 삽입
                        cur.execute("""
                            INSERT INTO congestion (
                                platform_station_ID, 
                                platform_bound_to, 
                                time_slot, 
                                congest_status
                            ) VALUES (%s, %s, %s, %s)
                        """, (
                            congestion_data.platform_station_ID,
                            congestion_data.platform_bound_to,
                            congestion_data.time_slot.strftime('%H:%M:%S'),
                            congestion_data.congest_status
                        ))

                except ValidationError as e:
                    raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"Value error in row {station_id}: {str(e)}")

            conn.commit()
            return {"message": "Congestion data uploaded successfully"}
        except Exception as e:
            conn.rollback()
            if isinstance(e, pymysql.Error):
                raise HTTPException(status_code=400, detail="Database Bad Request")
            else:
                raise HTTPException(status_code=500, detail=str(e))

@router.get("/{line_id}/export/stations")
async def export_stations(line_id: int):
    with get_db_connection() as (conn, cur):
        try:
            # 해당 라인의 역 정보와 소요시간 조회
            cur.execute("""
                SELECT s.ID, s.name, e.ET
                FROM station s
                LEFT JOIN eta e ON s.ID = e.station_ID
                WHERE s.line_ID = %s
                ORDER BY s.ID
            """, (line_id,))
            
            # CSV 행 생성
            csv_rows = []
            # 헤더 추가
            csv_rows.append(','.join(['역번호', '역명', '소요시간']))
            
            rows = cur.fetchall()
            for row in rows:
                et_time = row[2]
                if isinstance(et_time, timedelta):
                    total_seconds = int(et_time.total_seconds())
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    et_time = time(hours, minutes, seconds)
                
                row_data = [
                    str(row[0]),  # 역번호
                    row[1],       # 역명
                    et_time.strftime('%M:%S') if et_time else '00:00'  # 소요시간
                ]
                csv_rows.append(','.join(row_data))
            
            # 모든 행을 줄바꿈으로 연결하고 EUC-KR로 인코딩
            csv_content = '\n'.join(csv_rows).encode('euc-kr')
            
            return Response(
                content=csv_content,
                media_type="application/octet-stream",
                headers={
                    'Content-Disposition': f'attachment; filename="stations_line_{line_id}.csv"',
                    'Content-Type': 'application/octet-stream'
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/{line_id}/export/congestion")
async def export_congestion(line_id: int):
    # 시간대 생성 (5:30부터 0:30까지, 30분 간격)
    time_slots = []
    current_time = time(5, 30)
    while current_time != time(0, 30):
        time_slots.append(current_time)
        hours = current_time.hour
        minutes = current_time.minute + 30
        if minutes >= 60:
            hours = (hours + 1) % 24
            minutes = 0
        current_time = time(hours, minutes)
    time_slots.append(time(0, 30))

    csv_rows = []
    # CSV 헤더 작성
    header = ['역번호', '역명', '상하구분'] + [t.strftime('%H:%M') for t in time_slots]
    csv_rows.append(','.join(map(str, header)))
    
    with get_db_connection() as (conn, cur):
        try:
            # 해당 라인의 역 목록 조회
            cur.execute("""
                SELECT DISTINCT s.ID, s.name, p.bound_to
                FROM station s
                JOIN platform p ON s.ID = p.station_ID
                WHERE s.line_ID = %s
                ORDER BY s.ID, p.bound_to
            """, (line_id,))
            
            stations = cur.fetchall()
            
            # 각 역의 혼잡도 데이터 조회 및 CSV 행 작성
            for station in stations:
                station_id, station_name, bound_to = station
                bound_to_str = '상선' if bound_to == 0 else '하선'
                
                # MySQL의 올바른 시간 포맷 사용
                cur.execute("""
                    SELECT LEFT(time_slot, 5) as time_slot, congest_status
                    FROM congestion
                    WHERE platform_station_ID = %s AND platform_bound_to = %s
                    ORDER BY time_slot
                """, (station_id, bound_to))
                
                congestion_data = dict(cur.fetchall())
                
                # CSV 행 데이터 생성
                row_data = [station_id, station_name, bound_to_str]
                for slot in time_slots:
                    formatted_slot = slot.strftime('%H:%M')
                    row_data.append(congestion_data.get(formatted_slot, 0))
                
                csv_rows.append(','.join(map(str, row_data)))
            
            # 모든 행을 줄바꿈으로 연결하고 EUC-KR로 인코딩
            csv_content = '\n'.join(csv_rows).encode('euc-kr')
            
            return Response(
                content=csv_content,
                media_type="application/octet-stream",
                headers={
                    'Content-Disposition': f'attachment; filename="congestion_line_{line_id}.csv"',
                    'Content-Type': 'application/octet-stream'
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{line_id}/delete/stations")
async def delete_stations(line_id: int):
    with get_db_connection() as (conn, cur):
        try:
            cur.execute("DELETE FROM garage WHERE line_ID = %s", (line_id,))
            cur.execute("DELETE FROM eta WHERE station_ID IN (SELECT ID FROM station WHERE line_ID = %s)", (line_id,))
            cur.execute("DELETE FROM station WHERE line_ID = %s", (line_id,))
            conn.commit()
            return {"message": "Stations deleted successfully"}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{line_id}/delete/congestion")
async def delete_congestion(line_id: int):
    with get_db_connection() as (conn, cur):
        try:
            cur.execute("DELETE FROM congestion WHERE platform_station_ID IN (SELECT ID FROM station WHERE line_ID = %s)", (line_id,))
            cur.execute("DELETE FROM platform WHERE station_ID IN (SELECT ID FROM station WHERE line_ID = %s)", (line_id,))
            conn.commit()
            return {"message": "Congestion data deleted successfully"}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
