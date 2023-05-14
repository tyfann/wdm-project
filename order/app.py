import ast
import json
import os
import atexit

from flask import Flask, jsonify, Response
import redis
import requests

gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create/<user_id>')
def create_order(user_id: str):
    order_id = str(db.incr('order_id'))
    # create an empty order
    order = {'order_id': order_id, 'user_id': user_id, 'items': [], 'payment': False, 'amount': 0}
    # save the order in the database
    db.hset('orders', order_id, str(order))
    # return the order id
    return jsonify(order), 200


@app.delete('/remove/<order_id>')
def remove_order(order_id: str):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if None in order:
        return "No such order", 400
    else:
        db.hdel('orders', order_id)
        return "Successfully delete the order{order_id}", 200


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id: str, item_id: str):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if None in order:
        return "No such order", 400
    elif order['payment']:
        return "Order already checked out", 401
    else:
        item = requests.get(f"{gateway_url}/stock/find/{item_id}").json()
        if not item:
            return "No such item in the stock", 400
        if int(item['stock']) <= 0:
            return "Not enough stock for this item", 400
        order['amount'] = int(order['amount']) + int(item['price'])
        order['items'].append(item_id)
        db.hset('orders', order_id, str(order))
        return "Success", 202


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id: str, item_id: str):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if None in order:
        return "No such order", 400
    if order['payment']:
        return "Order already checked out", 401
    if len(order['items']) == 0:
        return "No items", 401
    else:
        order['items'].remove({item_id})
        item = requests.get(f"{gateway_url}/stock/find/{item_id}").json()
        order['amount'] -= int(item['price'])
        db.hset('orders', order_id, str(order))
        return "Success", 203


@app.get('/find/<order_id>')
def find_order(order_id: str):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if not order:
        return "No such order", 400
    else:
        return jsonify(order), 200


@app.post('/checkout/<order_id>')
def checkout(order_id: str):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if not order:
        return "No such order", 400
    elif not order['items']:
        return "No items in the order", 400
    elif order['payment']:
        return "Order already checked out", 401
    else:
        user_id = order['user_id']
        user = requests.get(f"{gateway_url}/payment/find_user/{user_id}").json()
        credit = user['credit']
        total_amount = order['amount']
        items = order['items']
        if credit >= total_amount:
            requests.post(f"{gateway_url}/payment/pay/{user_id}/{order_id}/{total_amount}")
            for i in items:
                requests.post(f"{gateway_url}/stock/subtract/{i}/{1}")
            order['payment'] = True
            db.hset('orders', order_id, str(order))
            return "Success", 201
        else:
            return "Not enough credit", 400
