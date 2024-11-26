from settings import DATABASE_HOST, DATABASE_ID, DATABASE_PASSWORD, DATABASE_NAME
import pymysql
from contextlib import contextmanager

def mysql_create_session():
    conn = pymysql.connect(host=DATABASE_HOST, user=DATABASE_ID, password=DATABASE_PASSWORD, db=DATABASE_NAME, charset='utf8')
    cur = conn.cursor()
    return conn, cur

@contextmanager
def get_db_connection():
    conn, cur = mysql_create_session()
    try:
        yield conn, cur
    finally:
        conn.close()

