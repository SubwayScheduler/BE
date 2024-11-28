from fastapi import APIRouter, Depends, HTTPException, Depends
from typing import List
from database import mysql_create_session, get_db_connection
from auth import get_current_user

from schemas import Train, TrainCreate, TrainUpdate
from typing import Optional
import pymysql

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

# 호선과 수용인원에 따른 열차 조회
@router.get("/")
def search_train(line_id: Optional[int] = None, capacity: int = 0):
    with get_db_connection() as (conn, cur):
        try:
            sql = "SELECT * FROM train"
            if line_id:
                sql += " WHERE Line_ID = %s AND capacity > %s"
                cur.execute(sql, (line_id, capacity))
            else:
                cur.execute(sql)
            
            columns = [column[0] for column in cur.description]
            result = []
            for row in cur.fetchall():
                result.append(dict(zip(columns, row)))
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# 열차 생성
@router.post("/")
def create_train(train: TrainCreate):
    with get_db_connection() as (conn, cur):
        try:
            sql = "INSERT INTO train (capacity, Line_ID) VALUES (%s, %s)"
            cur.execute(sql, (train.capacity, train.Line_ID))
            conn.commit()
            return {"message": "Train created successfully"}
        except pymysql.Error as e:
            conn.rollback()
            if e.args[0] == 1452:
                raise HTTPException(status_code=404, detail="No Such Line ID")
            elif e.args[0] == 3819:
                raise HTTPException(status_code=400, detail="Capacity must be positive")
            else:
                raise HTTPException(status_code=500, detail=str(e))

# 열차 수정
@router.put("/{train_id}")
def update_train(train_id: int, train: TrainUpdate):
    with get_db_connection() as (conn, cur):
        try:
            sql = "UPDATE train SET capacity = %s, Line_ID = %s WHERE ID = %s"
            cur.execute(sql, (train.capacity, train.Line_ID, train_id))
            conn.commit()
            return {"message": "Train updated successfully"}
        except pymysql.Error as e:
            conn.rollback()
            if e.args[0] == 1452:
                raise HTTPException(status_code=404, detail="No Such Line ID")
            elif e.args[0] == 3819:
                raise HTTPException(status_code=400, detail="Capacity must be positive")
            else:
                raise HTTPException(status_code=500, detail=str(e))

# 열차 삭제
@router.delete("/{train_id}")
def delete_train(train_id: int):
    with get_db_connection() as (conn, cur):
        try:
            sql = "DELETE FROM train WHERE ID = %s"
            cur.execute(sql, (train_id,))
            conn.commit()
            return {"message": "Train deleted successfully"}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
