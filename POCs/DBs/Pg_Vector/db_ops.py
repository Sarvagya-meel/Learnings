"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 16/06/25
"""
import os
from typing import Any
import psycopg

def get_connection_str(**kwargs: Any) -> str:
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    database = os.getenv('DB_DATABASE')
    connection_str =  f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return connection_str

def get_connection(**kwargs: Any) -> str:
    connection_str = get_connection_str(**kwargs)
    connection = psycopg.connect(connection_str)
    return connection

if __name__ == '__main__':
    print('Python')