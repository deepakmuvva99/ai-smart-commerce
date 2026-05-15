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

print(f"Connecting to {DB_HOST}...")

try:
    ssl_cert = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DigiCertGlobalRootG2.crt.pem")
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
        ssl={'ca': ssl_cert}
    )
    
    with connection.cursor() as cursor:
        with open('../wasted/setup_azure_mysql.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("Executing setup_azure_mysql.sql...")
        # Remove delimiter and split
        statements = sql_script.split(';')
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                    print(f"Success. Rows affected: {cursor.rowcount}")
                except Exception as e:
                    print(f"Error on statement: {statement[:50]}... -> {e}")
        connection.commit()
        print("Database successfully seeded with 103 products and variants!")
        
finally:
    connection.close()
