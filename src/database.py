import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("traffic.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            lane1 INTEGER,
            lane2 INTEGER,
            emergency INTEGER
        )
    """)

    conn.commit()
    conn.close()


def insert_data(lane1, lane2, emergency):
    print("Saving to DB:", lane1, lane2, emergency)

    conn = sqlite3.connect("traffic.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO traffic_data (time, lane1, lane2, emergency)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().strftime("%H:%M:%S"), lane1, lane2, int(emergency)))

    conn.commit()
    conn.close()