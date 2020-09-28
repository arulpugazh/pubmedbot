import os
import psycopg2
from gcputils import get_db_ip

db_user = os.environ["DB_USER"]
db_pass = os.environ["DB_PASS"]
db_name = os.environ["DB_NAME"]


def get_new_db_connection():
    try:
        conn = psycopg2.connect(user=db_user,
                                password=db_pass,
                                host=get_db_ip(),
                                port="5432",
                                database=db_name)
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(e)
