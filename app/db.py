import sqlite3
import random
from datetime import datetime, timedelta
import sys


def create_db(db: str, table: str):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table};")
    cur.execute(f"""CREATE TABLE {table}(
        id integer primary key autoincrement, 
        system, timestamp DATETIME, category, text);""")
    conn.commit()


def generate_data(n: int):
    systems = [
        "ALITPC",
        "ALITRD",
        "ALITOF",
        "ATLRPC",
        "ATLTGC",
        "ATLMDT",
        "CMSDT",
        "CMSRPC",
        "CMSCSC",
        "LHBRI1",
        "LHBRI2",
        "LHBMWP",
    ]
    categories = ["unProcessAlarm", "unProcessWarning", "PLCAlarm", "PGSAlarm"]
    messages = ["Value outside range", "Bad Communication", "Connection issues"]
    now = datetime.now()
    last_year = now - timedelta(days=365)
    random_data = []
    for i in range(n):
        random_system = random.choice(systems)
        random_category = random.choice(categories)
        random_epoch = random.randrange(
            int(last_year.timestamp()), int(now.timestamp())
        )
        random_timestamp = datetime.fromtimestamp(random_epoch)
        random_messages = random.choice(messages)
        random_text = f"""{random_timestamp} - {random_system} - {random_category} - {random_messages}"""
        random_data.append(
            (random_system, random_timestamp, random_category, random_text)
        )
    return random_data


def insert_data(db: str, table: str, data: list[tuple]):
    """Insert data in the table"""
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.executemany(f"INSERT INTO alarms VALUES (NULL, ?, ?, ?, ?)", data)
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    random_data = generate_data(n=10_000)
    create_db(db="db.sqlite", table="alarms")
    insert_data(db="db.sqlite", table="alarms", data=random_data)
