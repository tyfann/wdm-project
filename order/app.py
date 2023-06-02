import ast

from flask import Flask, jsonify, Response, g, request

import requests
import random

import cni

app = Flask("order-service")

stock_url = "http://stock-service:5000"
payment_url = "http://payment-service:5000"


#  This file does not connect to DB directly, just send your SQL query to connectionI, and connectionI will send the
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


@app.post('/create/<user_id>')
def create_order(user_id: str):
    while True:
        order_id = random.randrange(0, 9223372036854775807)  # Cockroachdb max and min INT values (64-bit)
        response = cni.query(
            "INSERT INTO ORDERS (order_id, user_id, paid, total_cost) VALUES (%s,%s,FALSE,0) RETURNING order_id",
            [order_id, user_id], g.connection)
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200


@app.delete('/remove/<order_id>')
def remove_order(order_id: str):
    if not g.cni_connected:
        g.connectionStr = cni.start_transaction()
        g.connection = tuple(g.connectionStr.split(':'))

    # ORDER_DETAILS to store the information of one order (order_id,item_id,amount)
    _, status_code = cni.get_response("DELETE FROM ORDER_DETAILS WHERE order_id=%s", [order_id], g.connection)
    if status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return

    _, status_code = cni.get_response("DELETE FROM ORDERS WHERE order_id=%s", [order_id], g.connection)
    if status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    if not g.cni_connected:
        cni.commit_transaction(g.connection)
    return cni.success_response


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id: str, item_id: str):
    if not g.cni_connected:
        g.connectionStr = cni.start_transaction()
        g.connection = tuple(g.connectionStr.split(':'))

    data, status_code = cni.get_response(
        "INSERT INTO ORDER_DETAILS (order_id, item_id, count) VALUES (%s,%s,1) ON CONFLICT (order_id, item_id) DO UPDATE SET count = ORDER_DETAILS.count+1",
        [order_id, item_id], g.connection)
    if status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    response = requests.get(f"{stock_url}/find/{item_id}", headers={"cn": g.connectionStr})
    if response.status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response
    price = response.json()["price"]  # todo!确定payment里面的名称

    data, status_code = cni.get_response("UPDATE ORDERS SET total_cost=total_cost+%s WHERE order_id=%s",
                                         [price, order_id], g.connection)
    if status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    if not g.cni_connected:
        cni.commit_transaction(g.connection)
    return cni.success_response


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id: str, item_id: str):
    if not g.cni_connected:
        g.connectionStr = cni.start_transaction()
        g.connection = tuple(g.connectionStr.split(':'))

    data, status_code = cni.get_response(
        "UPDATE ORDER_DETAILS SET count=count-1 WHERE order_id=%s AND item_id=%s RETURNING count",
        [order_id, item_id], g.connection)
    if status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response
    if data["count"] == 0:
        cni.query("DELETE FROM ORDER_DETAILS WHERE order_id=%s AND item_id=%s",
                  [order_id, item_id], g.connection)

    response = requests.get(f"{stock_url}/find/{item_id}", headers={"cn": g.connectionStr})
    if response.status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response
    price = response.json()["price"]

    data, status_code = cni.get_response("UPDATE ORDERS SET total_cost=total_cost-%s WHERE order_id=%s",
                                         [price, order_id], g.connection)
    if status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    if not g.cni_connected:
        cni.commit_transaction(g.connection)
    return cni.success_response


@app.get('/find/<order_id>')
def find_order(order_id: str):
    return cni.get_response(
        "SELECT %s AS order_id, (SELECT paid FROM ORDERS WHERE order_id=%s) AS paid, coalesce(json_object_agg(item_id::string, count), '{}'::json) AS items, (SELECT user_id FROM ORDERS WHERE order_id=%s) AS user_id, (SELECT total_cost FROM ORDERS WHERE order_id=%s) AS total_cost FROM ORDER_DETAILS WHERE order_id=%s",
        [order_id, order_id, order_id, order_id], g.connection)


# checkout函数中应当判断用户需要购买的item在stock中是否大于等于当前的购买需求，如果没满足，则需要返回checkout失败的信息
@app.post('/checkout/<order_id>')
def checkout(order_id: str):
    if not g.cni_connected:
        g.connectionStr = cni.start_transaction()
        g.connection = tuple(g.connectionStr.split(':'))

    data, status_code = cni.get_response("SELECT user_id, total_cost FROM ORDERS WHERE order_id=%s",
                                    [order_id], g.connection)
    if status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response
    user_id = data["user_id"]
    total_price = data["total_cost"]

    response = requests.post(f"{payment_url}/pay/{user_id}/{order_id}/{total_price}",
                             headers={"cn": g.connectionStr})
    if response.status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    data, status_code = cni.get_response(
        "SELECT coalesce(json_object_agg(item_id::string, count), '{}'::json) AS items FROM ORDER_DETAILS WHERE order_id=%s",
        [order_id], g.connection)
    if status_code != 200:
        if not g.cni_connected:
            cni.cancel_transaction(g.connection)
        return cni.fail_response
    items = data["items"]

    for item_id, count in items.items():
        response = requests.post(f"{stock_url}/subtract/{item_id}/{count}", headers={"cn": g.connectionStr})
        if response.status_code != 200:
            if not g.cni_connected:
                cni.cancel_transaction(g.connection)
            return cni.fail_response

    if not g.cni_connected:
        cni.commit_transaction(g.connection)
    return cni.success_response


if __name__ == '__main__':
    # host 0.0.0.0 to listen to all ip's
    app.run(host='0.0.0.0', port=5000)
