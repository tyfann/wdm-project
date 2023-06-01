import ast
import json
import os
import atexit

from flask import Flask, jsonify, Response
import redis
import requests

app = Flask("order-service")

# TODO: This file does not need to connect to DB directly, just send your SQL query to CMI, and CMI will send the
#  query to db_connector such that the query is executed in the DB
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


# checkout函数中应当判断用户需要购买的item在stock中是否大于等于当前的购买需求，如果没满足，则需要返回checkout失败的信息
@app.post('/checkout/<order_id>')
def checkout(order_id: str):
    order = ast.literal_eval(db.hget('orders', order_id).decode('utf-8'))
    if not order:
        return "No such order", 400
    elif not order['items']:
        return "No items in the order", 401
    elif order['payment']:
        return "Order already checked out", 402
    else:
        item_counts = {}
        stocks = {}
        items = order['items']
        for i in items:
            if i in item_counts:
                item_counts[i] += 1
            else:
                item_counts[i] = 1
            item = requests.get(f"{gateway_url}/stock/find/{i}").json()
            stocks[i] = item['stock']
            if not item or int(item['stock']) < 1:
                return "Checkout failed: Item '{}' is out of stock.".format(i), 404

        for item, count in item_counts.items():
            if count > int(stocks[item]):
                return "Checkout failed: Item '{}' is out of stock.".format(item), 404

        user_id = order['user_id']
        user = requests.get(f"{gateway_url}/payment/find_user/{user_id}").json()
        credit = user['credit']
        amount = order['amount']
        if credit >= amount:
            requests.post(f"{gateway_url}/payment/pay/{user_id}/{order_id}/{amount}")
            for i in items:
                requests.post(f"{gateway_url}/stock/subtract/{i}/{1}")
            order['payment'] = True
            db.hset('orders', order_id, str(order))
            return "Success", 201
        else:
            return "Not enough credit", 403
