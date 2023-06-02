
from flask import Flask, request, jsonify, make_response
from psycopg2 import pool
import os


app = Flask(__name__)
ip = os.getenv('MY_POD_IP')
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
    return make_response(response, 200)


# This function should receive the SQL sent from CMI and execute it
@app.post('/exec/<conn_id>')
def execute_transaction(conn_id):
    # We get the query here
    connection = connections[conn_id]
    jsons = request.json
    query = jsons["query"]
    # We start to execute the transaction from below
    cursor = connection.cursor()  # cursor is used to start a transaction
    try:
        cursor.execute(query)
    except Exception as error_message:
        return make_response(jsonify(str(error_message) + "Error happens when executing the query"), 500)
    # If the SQL query is not reading data from DB, the description is NONE
    if cursor.description is not None:
        # TODO: If we need the column name, we should wrap them into a dictionary
        result_dict = {}
        results = cursor.fetchall()
    else:
        results = cursor.fetchall()
    cursor.close()
    return make_response(results, 200)


@app.post('/commit/<conn_id>')
def commit_transaction(conn_id):
    connection = connections[conn_id]
    connection.commit()
    del connections[conn_id]
    pool.putconn(connection)
    return make_response("message:Commit Success", 200)


@app.post('/cancel/<conn_id>')
def cancel_transaction(conn_id):
    connection = connections[conn_id]
    connection.rollback()
    del connections[conn_id]
    pool.putconn(connection)

    return make_response("message=Cancel Success", 200)


if __name__ == '__main__':
    # host 0.0.0.0 to listen to all ip's
    app.run(host='0.0.0.0', port=5001)
