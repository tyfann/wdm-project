import requests
from psycopg2 import pool
from flask import Response

URL = "http://localhost:5000"
##DBURL
# db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
# db_url = "postgresql://root@cockroachdb-public:26257/defaultdb?sslmode=disable"
db_url = "postgresql://yufan:wejheJLUEhJ6OEDfq-NA5w@cuddly-bunny-7966.8nj.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"

pool = pool.SimpleConnectionPool(1, 30, db_url)

DONE_FALSE = Response(
    response='{"done": false}',
    status=400,
    mimetype="application/json")
DONE_TRUE = Response(
    response='{"done": true}',
    status=200,
    mimetype="application/json")


class ReturnType(object):
    pass


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
        res = ReturnType()
        res.status_code = 400
        res.json = lambda: error_message
        return res

    cursor = connection.cursor()

    try:
        cursor.execute(db_query, param)
    except Exception as error_message_1:
        print(error_message_1)
        cursor.close()
        connection.rollback()
        pool.putconn(connection)

        res = ReturnType()
        res.status_code = 500
        error = error_message_1
        res.json = lambda: error
        return res

    if cursor.description is None:
        results = cursor.fetchall()
    else:
        # zip them in the dictionary
        results = [to_dict(cursor, row) for row in cursor.fetchall()]

    #

    cursor.close()
    connection.commit()
    pool.putconn(connection)

    res = ReturnType()
    res.status_code = 200
    res.json = lambda: results

    return res


def get_response(db_query, param, connector):
    if db_query.split(' ')[0] != 'SELECT':
        db_query = f"{db_query} RETURNING TRUE AS done;"
    response = query(db_query, param, connector)

    if response.status_code == 200:
        result = response.json()
        # 判断result是否为list类型
        if isinstance(result, list):
            if len(result) == 0:
                return "Fail", 400
            elif len(result) == 1:
                return result[0], 200
        else:
            if len(result) == 0:
                return "Fail", 400
            else:
                return result, 200
    return "Fail", 400


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
