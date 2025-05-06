from datetime import datetime, timedelta
from sqlalchemy import func

from celery.result import AsyncResult

from flask import current_app
from flaskr.models import Prescription, Patient, Pharmacy
from flaskr.extensions import db
from flaskr.tasks import send_rx

def get_all_pharmacy_patients(pharmacy_id, new_request_time=datetime.now() - timedelta(hours=24)):
    rows = (
        db.session.query(
            Patient.user_id,
            Patient.first_name,
            Patient.last_name,
            func.max(Prescription.created_at).label("last_prescribed")
        ).join(Prescription, Prescription.patient_id == Patient.user_id)
        .filter(Prescription.pharmacy_id == pharmacy_id)
        .group_by(Patient.user_id, Patient.first_name, Patient.last_name)
        .all()
    )

    new_patients = []
    other_patients = []
    for id, first_name, last_name, created_at in rows:
        obj = {
            'patient_id':   id,
            'patient_name': f"{first_name} {last_name}"
        }
        if created_at >= new_request_time:
            new_patients.append(obj)
        else:
            other_patients.append(obj)

    return {
        'new_patients':   new_patients,
        'other_patients': other_patients
    }

def add_pt_rx(pharmacy_id, patient_id, doctor_id, medications):
    # TODO: detect duplicates / make idempotent
    try:
        if current_app.config['FLASK_ENV'] in {'prod', 'production'}:
            import os, uuid
            from kombu import Connection, Producer, Exchange
            with Connection(os.getenv('QUEUE_URL')) as conn:
                with conn.channel() as channel:
                    prod = Producer(channel)
                    exchange = Exchange(
                        'prescription_queue', 
                        type='direct'
                    )
                    """
                        body=json.dumps({
                            'pharmacy_id': pharmacy_id, 
                            'patient_id': patient_id, 
                            'doctor_id': doctor_id, 
                            'medications': medications
                        }),
                        headers={
                            'lang': 'py',
                            'task': 'flaskr.tasks.send_rx',
                            'argsrepr': repr(args),
                            'kwargsrepr': repr(kwargs)

                        }
                    """
                    task_id = uuid()
                    prod.publish(
                        correlation_id=task_id,
                        retry=True,
                        retry_policy={
                            'interval_start': 0,
                            'interval_step': 2,
                            'interval_max': 30,
                            'max_retries': 10
                        },
                        exchange='prescription_queue',
                        routing_key='prescription_queue',
                        serializer='msgpack',
                        body=(
                            [],
                            {
                                'pharmacy_id': pharmacy_id, 
                                'patient_id': patient_id, 
                                'doctor_id': doctor_id, 
                                'medications': medications
                            },
                            {}
                        ),
                        headers={
                            'id': task_id,
                            'lang': 'py',
                            'task': 'flaskr.tasks.send_rx',
                            'root_id': None,
                            'parent_id': None,
                            'group': None,
                        }
                    )

        else:
            res: AsyncResult = current_app.extensions['celery'].send_task(
                "send_rx", 
                kwargs={
                    'pharmacy_id': pharmacy_id, 
                    'patient_id': patient_id, 
                    'doctor_id': doctor_id, 
                    'medications': medications
                }
            )
        """
        res: AsyncResult = send_rx.apply_async(
            kwargs={
                'pharmacy_id': pharmacy_id, 
                'patient_id': patient_id, 
                'doctor_id': doctor_id, 
                'medications': medications
            })
        """
    except Exception as e:
        raise e
    return res.status

def get_pharmacy_info(pharmacy_id):
    pharmacy = Pharmacy.query.filter_by(user_id=pharmacy_id).first()
    if not pharmacy:
        return None
    return pharmacy.to_dict()
