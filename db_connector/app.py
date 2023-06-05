
from flask import Flask, request, jsonify
from psycopg2 import pool
import os


app = Flask(__name__)
#ip = os.getenv('MY_POD_IP')
# ip = os.getenv('MY_POD_IP')
ip = 'localhost'
# db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
db_url = "postgresql://yufan:wejheJLUEhJ6OEDfq-NA5w@cuddly-bunny-7966.8nj.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"

# db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
conn_count = 0
pool = pool.SimpleConnectionPool(1, 100, db_url)
connections = {}


@app.get('/start_trans')
def start_transaction():
    global conn_count
    conn = pool.getconn()
    connections[conn_count] = conn
    response = f"{ip}:{conn_count}"
    conn_count += 1
    return response, 200


# This function should receive the SQL sent from CMI and execute it
@app.post('/exec/<conn_id>')
def execute_transaction(conn_id):
    # We get the query here
    connection = connections[int(conn_id)]
    jsons = request.json
    params = jsons["param"]
    query = jsons["db"]
    # We start to execute the transaction from below
    cursor = connection.cursor()  # cursor is used to start a transaction

    try:
        cursor.execute(query,params)
    except Exception as error_message:
        return "Fail", 400
    # If the SQL query is not reading data from DB, the description is NONE
    if cursor.description is None:
        results = cursor.fetchall()
    else:
        results = [to_dict(cursor, row) for row in cursor.fetchall()]
    cursor.close()
    if len(results) == 1:
        return results[0], 200
    return "Fail", 400


@app.post('/commit/<conn_id>')
def commit_transaction(conn_id):
    connection = connections[int(conn_id)]
    connection.commit()
    del connections[int(conn_id)]
    pool.putconn(connection)

    return "Success", 200


@app.post('/cancel/<conn_id>')
def cancel_transaction(conn_id):
    connection = connections[int(conn_id)]
    connection.rollback()
    del connections[int(conn_id)]
    pool.putconn(connection)

    return "Success", 200

def to_dict(cursor, row):
    return {col[0]: value for col, value in zip(cursor.description, row)}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
