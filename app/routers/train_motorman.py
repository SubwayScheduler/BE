from fastapi import APIRouter, Depends, HTTPException, Depends
from typing import List
from database import mysql_create_session, get_db_connection
from auth import get_current_user

from schemas import TrainMotorman, TrainMotormanCreate, TrainMotormanUpdate
from typing import Optional
import pymysql

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

# 열차 당 motorman 조회
@router.get("/by_train")
def search_drive_by_train(train_id: int):
    with get_db_connection() as (conn, cur):
        try:
            sql = "SELECT * FROM train_motorman WHERE Train_ID = %s"
            cur.execute(sql, (train_id,))

            columns = [column[0] for column in cur.description]
            result = []
            for row in cur.fetchall():
                result.append(dict(zip(columns, row)))
            return result
        except pymysql.Error as e:
            raise HTTPException(status_code=500, detail=str(e))

# motorman 당 열차 조회
@router.get("/by_motorman")
def search_drive_by_motorman(motorman_id: int):
    with get_db_connection() as (conn, cur):
        try:
            sql = "SELECT * FROM train_motorman WHERE Motorman_ID = %s"
            cur.execute(sql, (motorman_id,))

            columns = [column[0] for column in cur.description]
            result = []
            for row in cur.fetchall():
                result.append(dict(zip(columns, row)))
            return result
        except pymysql.Error as e:
            raise HTTPException(status_code=500, detail=str(e))

# 열차 배치 생성
@router.post("/")
def create_drive(drive: TrainMotormanCreate):
    with get_db_connection() as (conn, cur):
        try:
            sql = "INSERT INTO train_motorman (Train_ID, Motorman_ID) VALUES (%s, %s)"
            cur.execute(sql, (drive.Train_ID, drive.Motorman_ID))
            conn.commit()
            return {"message": "Train motorman created successfully"}
        except pymysql.Error as e:
            conn.rollback()
            if e.args[0] == 1452:
                raise HTTPException(status_code=404, detail="No Such Train ID or Motorman ID")
            else:
                raise HTTPException(status_code=500, detail=str(e))

# 열차 배치 삭제
@router.delete("/{train_id}/{motorman_id}")
def delete_drive(train_id: int, motorman_id: int):
    with get_db_connection() as (conn, cur):
        try:
            sql = "DELETE FROM train_motorman WHERE Train_ID = %s AND Motorman_ID = %s"
            cur.execute(sql, (train_id, motorman_id))
            conn.commit()
            return {"message": "Train motorman deleted successfully"}
        except pymysql.Error as e:
            raise HTTPException(status_code=500, detail=str(e))

