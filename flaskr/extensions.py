import os

from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flasgger import Swagger

from socketio import KombuManager
from celery import Celery, Task
from google.cloud.sql.connector import Connector, IPTypes

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()

    import celery_healthcheck
    celery_healthcheck.register(celery_app)
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
server_sess = Session()

## SocketIO stuff
# TODO: replace with environment variables
kombu_mgr = KombuManager(
    os.environ.get('QUEUE_URL'),
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
    engineio_logger=True,
    client_manager=kombu_mgr
)
