import requests
from psycopg2 import pool
from flask import Response, make_response, jsonify

db_url = ""
pool = pool.SimpleConnectionPool(1, 100, db_url)

DONE_TRUE = ""
DONE_FALSE = ""


def query(db, param, connection):
    if(connection):
        address, id = connection
        return requests.post(f"http://{address}:5000/exec/{id}", json= {"db": db, "param": param})
    else:
       initial_connection(db, param)


def initial_connection(db, param):
    try:
        connection = pool.getconn()
    except Exception as error_message:

        return False

    cursor = connection.crusor()
    try:
        cursor.execute(query)
    except Exception as error_message:
        return make_response(jsonify(str(error_message) + "Error happens when executing the query"), 500)

def get_one(db, param, connector = None):
    pass

def get_all(db, param, connector):
    pass

def get_status(db, param, connector):
    pass

def start_transaction():
    pass

def cancel_transaction(connector):
    pass

def committ_transaction(connector):
    pass