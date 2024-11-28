from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from database import mysql_create_session, get_db_connection
from datetime import timedelta
from auth import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, pwd_context

from schemas import Administrator, AdministratorCreate, AdministratorUpdate
import pymysql

router = APIRouter()

# 관리자 로그인
@router.post("/administrator/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_db_connection() as (conn, cur):
        try:
            sql = "SELECT password FROM administrator WHERE name = %s"
            cur.execute(sql, (form_data.username,))

            from_db = cur.fetchone()
            password_from_db = from_db[0]

            print(password_from_db)

            if not verify_password(form_data.password, password_from_db):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
            return {"access_token": access_token, "token_type": "bearer"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# 관리자 회원가입
@router.post("/administrator/signup")
async def signup(administrator: AdministratorCreate):
    with get_db_connection() as (conn, cur):
        try:
            # 비밀번호 해싱
            hashed_password = pwd_context.hash(administrator.password)
            
            sql = "INSERT INTO administrator (name, password) VALUES (%s, %s)"
            cur.execute(sql, (administrator.name, hashed_password))  # 해싱된 비밀번호 저장
            conn.commit()
            return {"message": "Administrator created successfully"}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))