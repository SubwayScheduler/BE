from fastapi import APIRouter, Depends, HTTPException, Depends
from typing import List
from database import mysql_create_session, get_db_connection
from auth import get_current_user
from schemas import Line, LineCreate, LineUpdate
import pymysql

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

# 검색 없이 모든 호선 조회
@router.get("/")
def search_line():
    with get_db_connection() as (conn, cur):
        try:
            sql = "SELECT * FROM line"
            cur.execute(sql)

            columns = [column[0] for column in cur.description]
            result = []
            for row in cur.fetchall():
                result.append(dict(zip(columns, row)))
            return result
        except pymysql.Error as e:
            raise HTTPException(status_code=500, detail=str(e))

# 호선 생성
@router.post("/")
def create_line(line: LineCreate):
    with get_db_connection() as (conn, cur):
        try:
            sql = "INSERT INTO line (name, route_shape) VALUES (%s, %s)"
            cur.execute(sql, (line.name, line.route_shape))
            conn.commit()
            return {"message": "Line created successfully"}
        except pymysql.Error as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))


# 호선 수정
@router.put("/{line_id}")
def update_line(line_id: int, line: LineUpdate):
    with get_db_connection() as (conn, cur):
        try:
            updates = []
            params = []
            
            if line.route_shape:
                updates.append("route_shape = %s")
                params.append(line.route_shape)
            if line.name:
                updates.append("name = %s")
                params.append(line.name)
                
            if not updates:  # 업데이트할 필드가 없는 경우
                raise HTTPException(status_code=400, detail="No fields to update")
                
            sql = f"UPDATE line SET {', '.join(updates)} WHERE ID = %s"
            params.append(line_id)
            
            cur.execute(sql, tuple(params))
                
            conn.commit()
            return {"message": "Line updated successfully"}
        except pymysql.Error as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))


# 호선 삭제
@router.delete("/{line_id}")
def delete_line(line_id: int):
    with get_db_connection() as (conn, cur):
        try:
            sql = "DELETE FROM line WHERE ID = %s"
            cur.execute(sql, (line_id,))
            conn.commit()
            return {"message": "Line deleted successfully"}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
