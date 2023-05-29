import json
import os
import atexit

from flask import Flask
import redis
import requests

import cmi

# TODO: This file does not need to connect to DB directly, just send your SQL query to CMI, and CMI will send the
#  query to db_connector such that the query is executed in the DB

app = Flask("payment-service")


@app.post('/create_user')
def create_user():
    user_id = db.incr('user_id')
    user = {'user_id': user_id, 'credit': 0}
    db.hset(f'user:{user_id}', mapping=user)
    return user, 200


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    user = db.hmget(f'user:{user_id}', ['credit'])
    if None in user:
        return None, 400
    else:
        user_json = {'user_id': user_id, 'credit': int(user[0])}
        return user_json, 201


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    user_str = f'user:{user_id}'
    if None in db.hmget(user_str, ['credit']):
        return "Fail", 401
    else:
        db.hincrby(user_str, key='credit', amount=amount)
        return "Success", 202


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    user_str = f'user:{user_id}'
    user = db.hmget(user_str, ['credit'])
    if int(amount) <= 0:
        return "Amount must be more than 0", 400
    if None in user:
        return "Fail, no such user", 401
    else:
        # find order
        # with requests.get(f"{gateway_url}/orders/find/{order_id}") as response:
        #     order = response.json()
        #     if not order:
        #         return "No such order", 400
        #     if order['payment']:
        #         return "Order has already paid", 401
        #     response.close()
        if int(user[0]) >= int(amount):
            db.hincrby(user_str, key='credit', amount=-1 * int(amount))
            # response.close()
            return "Success", 203
        else:
            # response.close()
            return "Fail, user has not enough credit", 402

    # order = requests.get(f"{gateway_url}/orders/find/{order_id}").json()
    # if not order:
    #     return "No such order", 400
    # if order['payment']:
    #     return "Order has already paid", 401
    # if int(user[0]) >= int(amount):
    #     db.hincrby(user_str, key='credit', amount=-1*int(amount))
    #     return "Success", 203
    # else:
    #     return "Fail, user has not enough credit", 402


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    user_str = f'user:{user_id}'
    user = db.hmget(user_str, ['user_id'])
    if not user:
        return "No such user", 400
    order = requests.get(f"{gateway_url}/orders/find_order/{order_id}").json()
    if not order:
        return "No such order", 400
    if not order['payment']:
        return "Order's payment is not started yet"
    else:
        items = order['items']
        for i in items:
            # add the items back to the stock
            requests.post(f"{gateway_url}/stock/add/{i}/{1}").json()
        # add the credit back to the user
        amount = order['amount']
        add_credit(user_id, amount)
        return f"Successfully cancel the payment of user{user_id},order{order_id}", 200


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    user_str = f'user:{user_id}'
    user = db.hmget(user_str, ['user_id'])
    if not user:
        return "No such user", 400
    order = requests.get(f"{gateway_url}/orders/find_order/{order_id}").json()
    if not order:
        return "No such order", 400
    return order['payment'], 201
