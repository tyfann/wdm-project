import psycopg2

db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
# db_url = "postgresql://yufan:wejheJLUEhJ6OEDfq-NA5w@cuddly-bunny-7966.8nj.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"
conn = psycopg2.connect(db_url)

with conn.cursor() as cur:
    cur.execute(
        "DROP TABLE IF EXISTS ITEMS;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE ITEMS (item_id INT PRIMARY KEY, item_price NUMERIC, item_stock INT);"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS ORDERS;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE ORDERS (order_id INT PRIMARY KEY, user_id INT, paid BOOLEAN, total_cost NUMERIC);"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS ORDER_DETAILS;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE ORDER_DETAILS (order_id INT, item_id INT, item_amount INT, CONSTRAINT \"primary\" PRIMARY KEY (order_id, item_id));"
    )
    conn.commit()
    cur.execute(
        "DROP TABLE IF EXISTS USERS;"
    )
    conn.commit()
    cur.execute(
        "CREATE TABLE USERS (user_id INT PRIMARY KEY, credit NUMERIC);"
    )
    conn.commit()

conn.close()