import os
import atexit

from flask import Flask
import redis
import requests

app = Flask("payment-service")

db: redis.Redis = redis.Redis(host=os.environ['REDIS_HOST'],
                              port=int(os.environ['REDIS_PORT']),
                              password=os.environ['REDIS_PASSWORD'],
                              db=int(os.environ['REDIS_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


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
    if None in user:
        return "Fail", 401
    else:
        if int(user[0]) >= amount:
            db.hincrby(user_str, key='credit', amount=-amount)
            return "Success", 202
        else:
            return "Fail", 402


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    pass


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    pass
