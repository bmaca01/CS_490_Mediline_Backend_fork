import os

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_jwt_extended.utils import decode_token
from flask_socketio import SocketIO, emit, join_room
from flasgger import Swagger

from socketio import KombuManager
from celery import Celery, Task
from celery.signals import task_success
from google.cloud.sql.connector import Connector, IPTypes


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC
connector = Connector(ip_type=ip_type, refresh_strategy="LAZY")
db = SQLAlchemy()
swag = Swagger(
    template_file=os.path.join(
        os.getcwd(), 'flaskr', 'docs', 'template.yml'
    ),
    parse=True
)

jwt = JWTManager()

## SocketIO stuff
# TODO: replace with environment variables
kombu_mgr = KombuManager(
    'amqp://abc:abc@localhost:5672/test_vhost',
    queue_options={
        'queue': 'prescription_queue',
        'routing_key': 'prescription_queue'
    }
)
sio = SocketIO(
    ping_timeout=60,
    cors_allowed_origins='*',
    always_connect=True, 
    namespaces='*',
    logger=True,
    client_manager=kombu_mgr
)
@sio.event(namespace='/test')
def connect(sid):
    print(f'connected: {sid}')
    emit('connected', {'sid': sid})

@sio.event(namespace='/test')
def disconnect(reason):
    print('disconnect ', reason)

@sio.on('foo', namespace='/test')
def handle_foo(sid, data):
    print(f'recieved from {sid}: {data}')
    return data, sid

@sio.on('create_something', namespace='/test')
def handle_create_something(json):
    print(f'data: {json}')
    emit('foo', json)
    return json

@task_success.connect
def handle_prescription_success(sender=None, result=None, **kwargs):
    target_pharm = result['pharmacy_id']
    #print(target_pharm)
    kombu_mgr.emit(
        'new_rx', 
        data=result, 
        namespace='/pharmacy',
        to=str(target_pharm)
    )

@sio.event(namespace='/pharmacy')
def connect():
    emit('connected to pharmacy')

@sio.on('join', namespace='/pharmacy')
def handle_token(data):
    #print(request.sid)
    #print(f'recieved data {data}')
    uid = decode_token(data)['sub']
    join_room(uid)

