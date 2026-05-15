import os
import urllib.parse
from dotenv import load_dotenv
import pymysql

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

try:
    ssl_cert = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DigiCertGlobalRootG2.crt.pem")
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        database=DB_NAME,
        ssl={'ca': ssl_cert}
    )
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, email, role FROM users")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
finally:
    connection.close()
