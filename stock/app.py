import random
from flask import Flask, jsonify, request, g

import cni

app = Flask("stock-service")


# TODO: This file does not need to connect to DB directly, just send your SQL query to CMI, and CMI will send the
#  query to db_connector such that the query is executed in the DB


@app.before_request
def before_request():
    g.connectionStr = request.headers.get("cn")
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
            "INSERT INTO ITEMS (item_id, item_price, item_stock) VALUES (%s,%s, 0) RETURNING item_id",
            [item_id, price], g.connection)
        if response.status_code == 200:
            result = response.get_json()
            return result, 200  # Maybe we need to jsonify(result[0]), we have errors here.


@app.get('/find/<item_id>')
def find_item(item_id: str):
    res, status = cni.get_response("SELECT item_stock as stock, item_price as price FROM ITEMS WHERE item_id=%s",
                       [item_id], g.connection)
    # TODO: The result from normal find_item and find_item in order/add_item is not identical.
    if status == 200:
        res["price"] = float(res["price"])
    return res, status


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    return cni.get_response(
        "UPDATE ITEMS SET item_stock = item_stock + %s WHERE item_id=%s AND item_stock + %s > item_stock",
        [amount, item_id, amount], g.connection)


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    return cni.get_response(
        "UPDATE ITEMS SET item_stock = item_stock - %s WHERE item_id=%s AND item_stock - %s >= 0",
        [amount, item_id, amount], g.connection)


if __name__ == '__main__':
    # host 0.0.0.0 to listen to all ip's
    app.run(host='0.0.0.0', port=5001,debug=True)
    #app.run(host='0.0.0.0', port=5002, debug=False)
    #app.run(host='0.0.0.0', port=5003, debug=False)
