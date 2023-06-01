from flask import Flask, request, g
import requests
import random
import re

from db_connector import cni

app = Flask("payment-service")


@app.before_request
def before_request():
    g.connectionStr = request.headers.get("connection")
    if g.connectionStr is not None:
        g.cni_connected = True
        g.connection = tuple(g.connectionStr.split(':'))
    else:
        g.cni_connected = False
        g.connection = None


@app.post('/create_user')
def create_user():
    while True:
        user_id = random.randrange(0, 9223372036854775807)  # Cockroachdb max and min INT values (64-bit)
        response = cni.query("INSERT INTO accounts (user_id, credit) VALUES (%s, 0) RETURNING user_id",
                            [user_id], g.connection)
        if response.status_code == 200:
            result = response.json()
            if len(result) == 1:
                return result[0], 200


@app.get('/find_user/<user_id>')
def find_user(user_id: int):
    res, status = cni.get_response("SELECT user_id, credit FROM accounts WHERE user_id=%s",
                              [user_id], g.connection)
    if status == 200:
        res["credit"] = float(res["credit"])
    return res, status


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    return cni.get_response("UPDATE accounts SET credit = credit + %s WHERE user_id=%s AND credit + %s >= credit",
                            [amount, user_id, amount], g.connection)


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    if not g.cni_connected:
        g.connectionStr = cni.start_transaction()
        g.connection = tuple(g.connectionStr.split(':'))

    _, status_code = cni.get_response(
        "UPDATE accounts SET credit = credit - CAST(%s AS NUMERIC) WHERE user_id=%s AND credit - CAST(%s AS NUMERIC) >= 0 AND CAST(%s AS NUMERIC) >= 0",
        [amount, user_id, amount, amount], g.connection)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    _, status_code = cni.get_response(
        "UPDATE orders SET paid = TRUE WHERE order_id=%s AND user_id=%s AND paid = FALSE",
        [order_id, user_id], g.connection)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    if not g.cni_connected:
        cni.commit_transaction(g.connection)
    return cni.success_response


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    if not g.cni_connected:
        g.connectionStr = cni.start_transaction()
        g.connection = tuple(g.connectionStr.split(':'))

    _, status_code = cni.get_response(
        "UPDATE accounts SET credit = credit + CAST((SELECT SUM(unit_price) FROM order_details WHERE order_id=%s) AS INTEGER) WHERE user_id=%s",
        [order_id, user_id], g.connection)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    _, status_code = cni.get_response("UPDATE orders SET paid = FALSE WHERE order_id=%s",
                                      [order_id], g.connection)
    if status_code != 200:
        if not g.already_using_connection_manager:
            cni.cancel_transaction(g.connection)
        return cni.fail_response

    if not g.already_using_connection_manager:
        cni.commit_transaction(g.connection)
    return cni.success_response


# Changed to GET based on project document
@app.get('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    return cni.get_response("SELECT paid FROM orders WHERE order_id=%s",
                       [order_id], g.connection)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)