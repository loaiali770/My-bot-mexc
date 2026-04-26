import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS balance (
    id INTEGER PRIMARY KEY,
    value REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS positions (
    symbol TEXT,
    entry REAL,
    max_price REAL
)
""")

conn.commit()

def get_balance():
    row = c.execute("SELECT value FROM balance WHERE id=1").fetchone()
    if row:
        return row[0]
    else:
        c.execute("INSERT INTO balance (id, value) VALUES (1, 100)")
        conn.commit()
        return 100

def update_balance(val):
    c.execute("UPDATE balance SET value=? WHERE id=1", (val,))
    conn.commit()

def get_positions():
    rows = c.execute("SELECT * FROM positions").fetchall()
    return {r[0]: {"entry": r[1], "max": r[2]} for r in rows}

def save_position(symbol, entry):
    c.execute("INSERT INTO positions VALUES (?, ?, ?)", (symbol, entry, entry))
    conn.commit()

def update_max(symbol, price):
    c.execute("UPDATE positions SET max_price=? WHERE symbol=?", (price, symbol))
    conn.commit()

def remove_position(symbol):
    c.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
    conn.commit()
