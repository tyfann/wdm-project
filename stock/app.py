import os
import atexit

from flask import Flask, jsonify
import redis


app = Flask("stock-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/item/create/<price>')
def create_item(price: int):
    item_id = db.incr('item_id')
    item = {'item_id': item_id, 'price': price, 'stock': 0}
    db.hset(f'item:{item_id}', mapping=item)
    return item, 200


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item = db.hmget(f'item:{item_id}', ['price', 'stock'])
    if None in item:
        return None, 400
    else:
        item_json = {'item_id': item_id, 'price': int(item[0]), 'stock': int(item[1])}
        return item_json, 201


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    item_str = f'item:{item_id}'
    if None in db.hmget(item_str, ['price', 'stock']):
        return "Fail", 401
    else:
        db.hincrby(item_str, key='stock', amount=amount)
        return "Success", 202





@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    item_str = f'item:{item_id}'
    item = db.hmget(item_str, ['price', 'stock'])
    if None in item:
        return "Fail", 401

    current_amount = item[1]
    if int(current_amount) < int(amount):
        return "Stock Not Enough!", 402
    else:
        db.hincrby(item_str, key='stock', amount=-int(amount))
        return "Success", 203
