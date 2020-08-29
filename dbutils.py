import os
import psycopg2
import sqlite3

db_user = os.environ["DB_USER"]
db_pass = os.environ["DB_PASS"]
db_name = os.environ["DB_NAME"]
db_host = os.environ["DB_HOST"]
cloud_sql_connection_name = os.environ["CLOUD_SQL_CONNECTION_NAME"]


def get_new_db_connection():
    # conn = psycopg2.connect(user=db_user,
    #                         password=db_pass,
    #                         host=db_host,
    #                         port="5432",
    #                         database=db_name)
    # cur = conn.cursor()
    conn = None
    try:
        conn = sqlite3.connect('pubmed.sqlite', timeout=60)
        cur = conn.cursor()
    except Exception as e:
        print(e)
    return conn, cur