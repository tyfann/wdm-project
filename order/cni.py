import requests
from psycopg2 import pool
from flask import Response, make_response

URL = "http://connector-service:5000"
##DBURL
# db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
pool = pool.SimpleConnectionPool(1, 30, db_url)


def query(db_query, param, connection):
    if (connection):
        address, id = connection
        return requests.post(f"http://{address}:5000/exec/{id}", json={"db": db_query, "param": param})
    else:
        return initial_connection(db_query, param)


def initial_connection(db_query, param):
    try:
        connection = pool.getconn()
    except Exception as error_message:
        print(error_message)
        return make_response(str(error_message) + "Error happens when executing the query", 400)

    cursor = connection.cursor()

    try:
        cursor.execute(db_query, param)
    except Exception as error_message_1:
        print(error_message_1)
        cursor.close()
        connection.rollback()
        pool.putconn(connection)

        return make_response(str(error_message_1) + "Error happens when executing the query", 400)

    if cursor.description is None:
        results = cursor.fetchall()
    else:
        # zip them in the dictionary
        results = [to_dict(cursor, row) for row in cursor.fetchall()]

    #

    cursor.close()
    connection.commit()
    pool.putconn(connection)
    if len(results) == 0:
        return make_response("message:Error when executing SQL query", 400)

    if len(results) == 1:
        return make_response(results[0], 200)

    return make_response('Status: Failure', 400)


def get_response(db_query, param, connector):
    if db_query.split(' ')[0] != 'SELECT':
        db_query = f"{db_query} RETURNING TRUE AS done;"
    response = query(db_query, param, connector)

    if response.status_code == 200:
        return response.json, 200
    return "Status: Failure", 400



def start_transaction():
    response = requests.get(f"{URL}/start_trans")
    while response.status_code != 200:
        response = requests.get(f"{URL}/start_trans")
    return response.content.decode("utf-8")


def cancel_transaction(connector):
    address, connector_id = connector
    while requests.post(f"http://{address}:5000/cancel/{connector_id}").status_code != 200:
        pass
    return


def commit_transaction(connector):
    address, connector_id = connector
    while requests.post(f"http://{address}:5000/commit/{connector_id}").status_code != 200:
        pass
    return


def to_dict(cursor, row):
    return {col[0]: value for col, value in zip(cursor.description, row)}
