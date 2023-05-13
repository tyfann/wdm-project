import ast
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
def create_order(user_id):
    order_id = db.incr('order_id')
    # create an empty order
    order = {'order_id': order_id, 'user_id': user_id, 'items': [], 'payment': False, 'amount': 0}
    # save the order in the database
    db.hset('orders', order_id, str(order))
    # return the order id
    return jsonify(order), 200


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if None in order:
        return "No such order", 401
    else:
        db.hdel('orders', order_id)


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if None in order:
        return "No such order", 401
    else:
        order['items'].append({'item_id': item_id})
        db.hset('orders', order_id, str(order))
        return "Success", 202


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if None in order:
        return "No such order", 401
    if len(order['items']) == 0:
        return "No items", 401
    else:
        order['items'].remove({'item_id': item_id})
        db.hset('orders', order_id, str(order))
        return "Success", 203


@app.get('/find/<order_id>')
def find_order(order_id):
    order = ast.literal_eval(db.hgetall('orders', order_id).decode('utf-8'))
    if not order:
        return "No such order", 401
    else:
        return jsonify(order), 204


@app.post('/checkout/<order_id>')
def checkout(order_id):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if not order:
        return "No such order", 401
    elif not order['items']:
        return "No items in the order", 401
    elif order['payment']:
        return "Order already checked out", 401
    else:
        items = order['items']
        for item_id in items:
            item = requests.get(f"{gateway_url}/stock/find/{item_id}").json()
            order['amount'] += int(item['price'])
            user_id = order['user_id']
            user = requests.get(f"{gateway_url}/payment/find_user/{user_id}").json()
            credit = user['credit']
            if credit >= order['amount']:
                order['payment'] = True
                db.hset('orders', order_id, str(order))
                return "Success", 205
            else:
                return "Not enough credit", 401
