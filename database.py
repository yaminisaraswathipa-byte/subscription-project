import sqlite3

def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT
    )
    """)

    # Create subscriptions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subscription_name TEXT,
        category TEXT,
        price REAL,
        billing_cycle TEXT,
        start_date TEXT,
        renewal_date TEXT
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()