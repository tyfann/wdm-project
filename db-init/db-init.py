import psycopg2

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
conn = psycopg2.connect(db_url)

with conn.cursor() as cur:
    cur.execute(
        "DROP TABLE IF EXISTS ITEM;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE ITEM (item_id INT PRIMARY KEY, item_price NUMERIC, item-stock INT);"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS Orders;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE Orders (order_id INT PRIMARY KEY, user_id INT, is_paid BOOLEAN, total_price NUMERIC);"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS order_detail;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE order_detail (order_id INT, item_id INT, item_amount INT, CONSTRAINT PK_order_item PRIMARY KEY (order_id, item_id));"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS users;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE users (user_id INT PRIMARY KEY, credit NUMERIC);"
    )
    conn.commit()

conn.close()