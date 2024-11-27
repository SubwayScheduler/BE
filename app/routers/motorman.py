# app/routers/motorman.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database import mysql_create_session, get_db_connection

from schemas import Motorman, MotormanCreate, MotormanUpdate

router = APIRouter()

@router.get("/")
def search_motorman(motorman_name: str = None ):
    with get_db_connection() as (conn, cur):
        try:
            if motorman_name:
                sql = "SELECT * FROM motorman WHERE name LIKE %s"
                cur.execute(sql, (f"%{motorman_name}%",))
            else:
                sql = "SELECT * FROM motorman"
                cur.execute(sql)

            columns = [column[0] for column in cur.description]
            result = []
            for row in cur.fetchall():
                result.append(dict(zip(columns, row)))
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_motorman(motorman: MotormanCreate):
    with get_db_connection() as (conn, cur):
        try:
            sql = "INSERT INTO motorman (name) VALUES (%s)"
            cur.execute(sql, (motorman.name,))
            conn.commit()
            new_id = cur.lastrowid
            return {"id": new_id, "message": "Motorman created successfully"}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))


@router.put("/{motorman_id}")
def update_motorman(motorman_id: int, motorman: MotormanUpdate):
    with get_db_connection() as (conn, cur):
        try:
            sql = "UPDATE motorman SET name = %s WHERE ID = %s"
            cur.execute(sql, (motorman.name, motorman_id))
            conn.commit()
            return {"message": "Motorman updated successfully"}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{motorman_id}")
def delete_motorman(motorman_id: int):
    with get_db_connection() as (conn, cur):
        try:
            sql = "DELETE FROM motorman WHERE ID = %s"
            cur.execute(sql, (motorman_id,))
            conn.commit()
            return {"message": "Motorman deleted successfully"}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
