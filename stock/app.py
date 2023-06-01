import os
import atexit
from random import random

from flask import Flask, jsonify, request, g
import redis

from db_connector import cni

app = Flask("stock-service")


# TODO: This file does not need to connect to DB directly, just send your SQL query to CMI, and CMI will send the
#  query to db_connector such that the query is executed in the DB


@app.before_request
def before_request():
    g.connectionStr = request.headers.get("connection")
    if g.connectionStr is not None:
        g.cni_connected = True
        g.connection = tuple(g.connectionStr.split(':'))
    else:
        g.cni_connected = False
        g.connection = None


@app.post('/item/create/<price>')
def create_item(price: int):
    while True:
        item_id = random.randrange(0, 9223372036854775807)  # Cockroachdb max and min INT values (64-bit)
        response = cni.query(
            "INSERT INTO stock (item_id, unit_price, stock_amount) VALUES (%s,%s, 0) RETURNING item_id",
            [item_id, price], g.connection)
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200


@app.get('/find/<item_id>')
def find_item(item_id: str):
    return cni.get_one("SELECT stock_amount as stock, unit_price as price FROM stock WHERE item_id=%s",
                       [item_id], g.connection)


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    return cni.get_status(
        "UPDATE stock SET stock_amount = stock_amount + %s WHERE item_id=%s AND stock_amount + %s > stock_amount",
        [amount, item_id, amount], g.connection)


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    return cni.get_status(
        "UPDATE stock SET stock_amount = stock_amount - %s WHERE item_id=%s AND stock_amount - %s >= 0",
        [amount, item_id, amount], g.connection)


if __name__ == '__main__':
    # host 0.0.0.0 to listen to all ip's
    app.run(host='0.0.0.0', port=5000)
